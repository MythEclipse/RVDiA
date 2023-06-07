import asyncio
import discord
import datetime
import time
import random
import json
from os import getenv, listdir, path
from discord.ui import View, Button, button
from discord import app_commands
from discord.ext import commands
from scripts.main import connectdb, check_blacklist, has_registered, level_up, send_level_up_msg

class GameInstance():
    def __init__(self, ctx:commands.Context, user1:discord.Member, user2, bot):
        # user2 is discord.Member if PvP, dict if PvE.
        self.user1 = user1
        self.user2 = user2
        self.user1_hp = 100
        try:
            self.user2_hp = self.user2['hp']

        except:
            self.user2_hp = 100

        self.running = False
        self.ctx = ctx
        self.bot = bot
        self.command_name = ctx.command.name

    async def gather_data(self):
        database = connectdb('Game')
        user1_data = database.find_one({'_id':self.user1.id})
        user1_stats = [user1_data['attack'], user1_data['defense'], user1_data['agility']]
        comp_data1 = {
            'stats': user1_stats,
            'hp': self.user1_hp
        }

        if self.command_name == "fight":
            # Fight = PvP
            user2_data = database.find_one({'_id':self.user2.id})
            if user2_data is None:
                await self.ctx.reply(f'Waduh! Sepertinya <@{self.user2.id}> belum membuat akun Land of Revolution!')
                raise Exception('Rival has no account!')
            
            user2_stats = [user2_data['attack'], user2_data['defense'], user2_data['agility']]
            comp_data2 = {
                'stats': user2_stats,
                'hp': self.user2_hp
            }

        else:
            user2_stats = [self.user2['atk'], self.user2['def'], self.user2['agl']]
            comp_data2 = {
                'stats':user2_stats,
                'hp':self.user2_hp
            }

        return [comp_data1, comp_data2] # List containing dict, feeling stressful


    def attack(self, dealer_stat:list, taker_stat:list, dealer_id:id, is_defending:bool):
        user_1_atk, user_1_def, user_1_agl = dealer_stat[0], dealer_stat[1], dealer_stat[2]
        user_2_atk, user_2_def, user_2_agl = taker_stat[0], taker_stat[1], taker_stat[2]

        if is_defending:
            user_2_def += 15

        damage = max(0, user_1_atk*(random.randint(70, 100) - user_2_def)/100)
        miss_chance = (user_2_agl - user_1_agl)*2 + 5
        hit_chance = 100 - miss_chance
        attack_chance = random.randint(0, 100)

        if hit_chance >= attack_chance:
            if dealer_id == self.user1.id: # Might work
                self.user2_hp = self.user2_hp - damage
            else:
                self.user1_hp = self.user1_hp - damage

            return damage
        
        else:
            return 0

    

    async def start(self):
        # Start -> Create Thread -> While loop (this is for later zzz)
        # How do I check if other game instances are runnin tho
        self.running = True
        datas = await self.gather_data()
        await self.ctx.reply('⚔️ Perang dimulai!') # I'll just use this for now
        await asyncio.sleep(2.7)

        user1_defending = False
        user2_defending = False
        while self.user1_hp > 0 and self.user2_hp > 0:
            await self.ctx.channel.send(f'<@{self.user1.id}> Giliranmu, ketik `attack`, `defend`, atau `end` di chat!')
            res_1 = await self.bot.wait_for('message', check = lambda r: r.author == self.user1 and r.channel == self.ctx.channel, timeout = 25.0) # Capekkkkk

            match res_1.content.lower():
                case "attack":
                    damage = self.attack(datas[0]['stats'], datas[1]['stats'], self.user1.id, user2_defending)
                    embed = discord.Embed(title=f'💥{self.user1.display_name} Menyerang!', color=self.user1.color)
                    if isinstance(self.user2, discord.Member):
                        embed.description = f"**`{damage}` Damage!**\nHP <@{self.user2.id}> tersisa `{self.user2_hp}` HP!"
                    else:
                        embed.description = f"**`{damage}` Damage!**\nHP {self.user2['name']} tersisa `{self.user2_hp}` HP!"
                    embed.set_thumbnail(url=self.user1.avatar.url)
                    await self.ctx.channel.send(embed=embed)
                    if user2_defending:
                        user2_defending = False

                case "defend":
                    user1_defending = True
                    embed = discord.Embed(title=f'🛡️{self.user1.display_name} Melindungi Diri!', color=self.user1.color)
                    embed.description = f"**Defense bertambah `+15` untuk serangan selanjutnya!**"
                    embed.set_thumbnail(url=self.user1.avatar.url)
                    await self.ctx.channel.send(embed=embed)

                case "end":
                    await self.ctx.channel.send(f'⛔ <@{self.user1.id}>  Mengakhiri perang.')
                    return

                case _:
                    await self.ctx.channel.send("Opsi tidak valid, giliran dilewatkan.")

            if self.user2_hp <= 0:
                await asyncio.sleep(2.5)
                break

            await asyncio.sleep(2.5)

            if isinstance(self.user2, discord.Member):
                await self.ctx.channel.send(f'<@{self.user2.id}> Giliranmu, ketik `attack`, `defend`, atau `end` di chat!')
                res_2 = await self.bot.wait_for('message', check = lambda r: r.author == self.user2 and r.channel == self.ctx.channel, timeout = 25.0)

                match res_2.content.lower():
                    case "attack":
                        damage = self.attack(datas[1]['stats'], datas[0]['stats'], self.user2.id, user1_defending)
                        embed = discord.Embed(title=f'💥{self.user2.display_name} Menyerang!', color=self.user2.color)
                        embed.description = f"**`{damage}` Damage!**\nHP <@{self.user1.id}> tersisa `{self.user1_hp}` HP!"
                        embed.set_thumbnail(url=self.user2.avatar.url)
                        await self.ctx.channel.send(embed=embed)
                        if user1_defending:
                            user1_defending = False

                    case "defend":
                        user2_defending = True
                        embed = discord.Embed(title=f'🛡️{self.user2.display_name} Melindungi Diri!', color=self.user2.color)
                        embed.description = f"**Defense bertambah `+15` untuk serangan selanjutnya!**"
                        embed.set_thumbnail(url=self.user2.avatar.url)
                        await self.ctx.channel.send(embed=embed)

                    case "end":
                        await self.ctx.channel.send(f'⛔ <@{self.user2.id}>  Mengakhiri perang.')
                        return

                    case _:
                        await self.ctx.channel.send("Opsi tidak valid, giliran dilewatkan.")

            else:
                choice = random.choice(['attack', 'defend'])
                match choice:
                    case "attack":
                        damage = self.attack(datas[1]['stats'], datas[0]['stats'], 1, user1_defending)
                        embed = discord.Embed(title=f'💥{self.user2["name"]} Menyerang!', color=0xff0000)
                        embed.description = f"**`{damage}` Damage!**\nHP <@{self.user1.id}> tersisa `{self.user1_hp}` HP!"
                        # ADD EMBED THUMBNAIL
                        await self.ctx.channel.send(embed=embed)
                        if user1_defending:
                            user1_defending = False

                    case "defend":
                        user2_defending = True
                        embed = discord.Embed(title=f'🛡️{self.user2["name"]} Melindungi Diri!', color=0xff0000)
                        embed.description = f"**Defense bertambah `+15` untuk serangan selanjutnya!**"
                        # ADD EMBED THUMBNAIL
                        await self.ctx.channel.send(embed=embed)


            await asyncio.sleep(2.5)

        if self.user1_hp > self.user2_hp:
            embed = discord.Embed(title=f"{self.user1.display_name} Menang!", color=0xffff00)
            embed.description = f"Dengan `{self.user1_hp}` HP tersisa!"
            embed.set_thumbnail(url = self.user1.avatar.url)
            embed.set_footer(text='Kamu memperoleh 15 koin dan 5 karma!')
            await self.ctx.channel.send(embed=embed)

        else:
            if isinstance(self.user2, discord.Member):
                embed = discord.Embed(title=f"{self.user2.display_name} Menang!", color=0xffff00)
                embed.description = f"Dengan `{self.user2_hp}` HP tersisa!"
                embed.set_thumbnail(url = self.user2.avatar.url)
                embed.set_footer(text='Kamu memperoleh 15 koin dan 5 karma!')
                await self.ctx.channel.send(embed=embed)

            else:
                embed = discord.Embed(title=f"Kamu Kalah!", color=0xff0000)
                embed.description = f"{self.user2['name']} menang dengan `{self.user2_hp}` HP tersisa!"
                # ADD EMBED THUMBNAIL
                embed.set_footer(text='Tip: Gunakan item dan skill spesial yang kamu miliki!')
                await self.ctx.channel.send(embed=embed)

        return

        
class ResignButton(View):
    def __init__(self, ctx:commands.Context):
        super().__init__(timeout=20)
        self.ctx = ctx
        self.value = None

    @button(label='Hapus Akun', style=discord.ButtonStyle.danger, custom_id='delacc')
    async def delete_account(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Kamu tidak diperbolehkan berinteraksi dengan tombol ini!", ephemeral=True)
            return
        database = connectdb('Game')
        data = database.find_one({'_id':interaction.user.id})
        database.find_one_and_delete({'_id':interaction.user.id})
        await interaction.response.send_message(f'Aku telah menghapus akunmu.\nSampai jumpa, `{data["name"]}`, di Land of Revolution!')
        self.value = True
        self.stop()

    @button(label='Batalkan', style=discord.ButtonStyle.green, custom_id='canceldel')
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Kamu tidak diperbolehkan berinteraksi dengan tombol ini!", ephemeral=True)
            return
        await interaction.response.send_message('Penghapusan akun dibatalkan.')
        self.value = False
        self.stop()

class ShopDropdown(discord.ui.Select):
    def __init__(self, page:int):
        self.page = page

        with open('./src/game/shop.json') as file:
            content = file.read()
            items = json.loads(content)

        options = []
        for index, item in enumerate(items):
            index = index+1
            if self.page == 1 and not index > 5:
                options.append(discord.SelectOption(
                                label = f"{index}. {item['name']}", 
                                description=f"Harga: {item['cost']} {item['paywith']}", 
                                value=item['_id']
                                )
                            )

        super().__init__(custom_id="shopdrop", placeholder="Mau beli apa?", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        with open('./src/game/shop.json') as file:
            content = file.read()
            items = json.loads(content)

        item_id = self.values[0]
        database = connectdb('Game')
        data = database.find_one({'_id':interaction.user.id})
        db_dict = {item['_id']: item for item in items}
        mongo_dict = {item['_id']: item for item in data['items']}

        matched_dict = db_dict[item_id]
        current_money = data['coins'] if matched_dict['paywith'] == "Koin" else data['karma']
        if current_money < matched_dict['cost']:
            return await interaction.response.send_message(f"Waduh!\n{matched_dict['paywith']}mu tidak cukup untuk membeli barang ini!")

        if item_id in db_dict and item_id in mongo_dict: # User already bought this item in the past

            filter_ = {'_id': interaction.user.id, 'items._id': item_id}
            update_ = {'$inc': {'items.$.owned': 1}}
            database.update_one(filter=filter_, update=update_)

            currency = 'coins' if matched_dict['paywith'] == "Koin" else 'karma'
            cost = matched_dict['cost']
            update_ = {'$inc': {currency: cost*-1}}
            database.update_one(filter=filter_, update=update_)

            await interaction.response.send_message(f"Pembelian berhasil!\nKamu telah membeli `{matched_dict['name']}`")

        else:
            currency = 'coins' if matched_dict['paywith'] == "Koin" else 'karma'
            cost = matched_dict['cost']
            del matched_dict['cost']
            del matched_dict['paywith']
            matched_dict['owned'] = 1
            database.update_one({'_id': interaction.user.id},
                                {'$push':{'items':matched_dict}})
            
            database.update_one({'_id': interaction.user.id}, {'$inc':{currency: cost*-1}}) # Second update, avoiding conflict

            await interaction.response.send_message(f"Pembelian berhasil!\nKamu telah membeli `{matched_dict['name']}`")

class EnemyDropdown(discord.ui.Select):
    def __init__(self):
        options = []
        json_files = [file for file in listdir('./src/game/enemies') if file.endswith('.json')]
        for file in json_files:
            name = path.splitext(file)[0]
            options.append(discord.SelectOption(
                label=name.title(),
                value=name
            ))
        super().__init__(custom_id="enemydrop", placeholder="Level Musuh", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        with open(f'./src/game/enemies/{self.values[0]}.json') as file:
            content = file.read()
            enemies = json.loads(content)
        
        embed = discord.Embed(title=f"Daftar Musuh", color=interaction.user.color)
        for index, enemy in enumerate(enemies):
            embed.add_field(
                name=f"{index}. {enemy['name']} ({self.values[0].upper()})",
                value=f"\"{enemy['desc']}\"\n**HP**: `{enemy['hp']}`\n**Attack**: `{enemy['atk']}`\n**Defense**: `{enemy['def']}`\n**Agility**: `{enemy['agl']}`",
                inline=False
                )
        embed.set_thumbnail(url = interaction.user.avatar.url) # Lazy, might add a placeholder later
        embed.set_footer(text="Kamu bisa melawan salah satu dari mereka dengan command battle!")
        await interaction.response.send_message(embed=embed, view=EnemyView())

class EnemyView(View):
    def __init__(self):
        super().__init__(timeout=30)
        self.add_item(EnemyDropdown())

class ShopView(View):
    def __init__(self, page):
        self.page = page
        super().__init__(timeout=20)
        self.add_item(ShopDropdown(self.page))

class Game(commands.Cog):
    """
    Kumpulan command game RPG RVDIA (Land of Revolution).
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name='game')
    @has_registered()
    @check_blacklist()
    async def game(self, ctx:commands.Context, *, user:discord.User=None):
        """
        Kumpulan command game RPG RVDIA. [GROUP]
        """
        user = user or ctx.author
        await self.account(ctx, user=user)
        pass

    @game.command(aliases=['reg'], description='Daftarkan akunmu ke Land of Revolution!')
    @app_commands.describe(name='Nama apa yang ingin kamu pakai di dalam gamenya?')
    @check_blacklist()
    async def register(self, ctx:commands.Context, *, name:str=None):
        """
        Daftarkan akunmu ke Land of Revolution!
        """
        name=name or ctx.author.name
        database = connectdb('Game')
        data = database.find_one({'_id':ctx.author.id})
        if data: return await ctx.reply('Kamu sudah memiliki akun game!')
        database.insert_one({
            '_id':ctx.author.id,
            'name':name,
            'level':1,
            'exp':0,
            'next_exp':50,
            'last_login':datetime.datetime.now(),
            'coins':100,
            'karma':10,             # Luck points
            'attack':10,
            'defense':7,
            'agility':8,
            'special_skills':[],    # Push JSON to here
            'items':[],
            'equipments':[]         # Push it to here also
        })
        await ctx.reply(f'Akunmu sudah didaftarkan!\nSelamat datang di Land of Revolution, **`{name}`**!')
    
    @game.command(description='Menghapuskan akunmu dari Land of Revolution.')
    @has_registered()
    @check_blacklist()
    async def resign(self, ctx:commands.Context):
        """
        Menghapuskan akunmu dari Land of Revolution.
        """
        view = ResignButton(ctx)
        await ctx.reply('Apakah kamu yakin akan menghapus akunmu?\nKamu punya 20 detik untuk menentukan keputusanmu.', view=view)
        await view.wait()
        if view.value is None:
            await ctx.channel.send('Waktu habis, penghapusan akun dibatalkan.')

    @game.command(aliases=['login'], description='Dapatkan bonus login harian!')
    @has_registered()
    @check_blacklist()
    async def daily(self, ctx:commands.Context):
        """
        Dapatkan bonus login harian!
        """
        database = connectdb('Game')
        data = database.find_one({'_id':ctx.author.id})
        last_login = data['last_login']
        current_time = datetime.datetime.now()
        delta_time = current_time - last_login

        next_login = last_login + datetime.timedelta(hours=24)
        next_login_unix = int(time.mktime(next_login.timetuple()))

        if delta_time.total_seconds() <= 24*60*60:
            return await ctx.reply(f'Kamu sudah login hari ini!\nKamu bisa login lagi pada <t:{next_login_unix}:f>')
        
        else:
            new_coins = random.randint(15, 25)
            new_karma = random.randint(1, 5)
            new_exp = random.randint(10, 20)
            database.find_one_and_update(
                {'_id':ctx.author.id},
                {'$inc':{'coins':new_coins, 'karma':new_karma, 'exp':new_exp}, '$set':{'last_login':datetime.datetime.now()}}
            )
            embed = discord.Embed(title='Bonus Harianmu', color=0x00FF00, timestamp=next_login)
            embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else getenv('normalpfp'))
            embed.description = f'Kamu mendapatkan:\n`{new_coins}` koin;\n`{new_karma}` karma;\n`{new_exp}` EXP!'
            embed.set_footer(text='Bonus selanjutnya pada ')
            await ctx.reply(embed=embed)

            if level_up(ctx):
                return await send_level_up_msg(ctx)
            
    @game.command(description='Lihat profil pengguna di Land of Revolution!')
    @app_commands.describe(user='Pengguna mana yang ingin dilihat akunnya?')
    @app_commands.rename(user='pengguna')
    @has_registered()
    @check_blacklist()
    async def account(self, ctx:commands.Context, *, user:discord.User=None):
        """
        Lihat profil pengguna di Land of Revolution!
        """
        # Plans: PIL profile pic, equipment & items should be seperate commands
        user = user or ctx.author
        database = connectdb('Game')
        data = database.find_one({'_id':user.id})

        # General data
        player_name = data['name']
        level = data['level']
        exp, next_exp = data['exp'], data['next_exp']
        last_login = data['last_login']

        # Stats & economy
        coins = data['coins']
        karma = data['karma']

        # Battle stats
        attack, defense, agility = data['attack'], data['defense'], data['agility']
        special_skills = data['special_skills']

        embed = discord.Embed(title=player_name, timestamp=last_login)
        embed.set_author(name='Info Akun Land of Revolution:')
        embed.description = f'Alias: {user}'
        embed.set_thumbnail(url=user.avatar.url if user.avatar else getenv('normalpfp'))

        embed.add_field(
            name=f'Level {level}', 
            value=f'EXP: `{exp}`/`{next_exp}`', 
            inline=False
            )

        embed.add_field(
            name=f'Status Keuangan',
            value=f'Koin: `{coins}`\nKarma: `{karma}`', 
            inline=False
            )

        embed.add_field(
            name=f'Statistik Tempur', 
            value=f'Attack: `{attack}`\nDefense: `{defense}`\nAgility: `{agility}`', 
            inline=False
            )
        
        embed.add_field(
            name='Skill Spesial',
            value=', '.join(special_skills) if not special_skills == [] else "Belum ada dikuasai.",
            inline=False
        )
        
        embed.set_footer(text='Login harian terakhir ')
        await ctx.reply(embed = embed)

    @game.command(description="Beli item atau perlengkapan perang!")
    @has_registered()
    @check_blacklist()
    async def shop(self, ctx:commands.Context):
        """
        Beli item atau perlengkapan perang!
        """
        # Plans: show details and make a paginator or something
        database = connectdb('Game')
        data = database.find_one({'_id':ctx.author.id})
        with open('./src/game/shop.json') as file:
            content = file.read()
            items = json.loads(content)

        embed = discord.Embed(title = 'Toko Xaneria', color=0xFFFF00)
        embed.description='"Hey, hey! Selamat datang. Silahkan, mau beli apa?"'
        embed.set_footer(text='Untuk membeli sebuah item, klik di bawah ini! v')
        embed.set_thumbnail(url=getenv('xaneria'))
        iix = [] # Track down how many indexes there are.
        owned = []
        for index, item in enumerate(items):
            index = index+1
            if not index > 5:
                try:
                    for key in data['items']:
                        if key['_id'] == item['_id']:
                            owned.append(key['owned'])
                except:
                    pass

                # Append 0 to owned until its length is equal to index
                while len(owned) < index:
                    owned.append(0)

                embed.add_field(
                    name=f"{index}. {item['name']}", 
                    value=f"**`{item['desc']}`**\n({item['func']})\n**Tipe:** {item['type']}\n**Harga:** {item['cost']} {item['paywith']}\n**Dimiliki:** {owned[index-1]}",
                    inline=False
                )
                iix.append(index)
        
        match max(iix):
            case 5:
                page = 1

            case _:
                page = 1

        view = ShopView(page)
        await ctx.reply(embed = embed, view=view)

    @game.command(description='Tantang seseorang ke sebuah duel!')
    @app_commands.describe(member='Siapa yang ingin kamu lawan?')
    @app_commands.rename(member='pengguna')
    @has_registered()
    @check_blacklist()
    async def fight(self, ctx:commands.Context, *, member:discord.Member):
        """
        Tantang seseorang ke sebuah duel!
        """
        if member.bot:
            return await ctx.reply('Bot tidak bisa melakukan perlawanan!')
        game = GameInstance(ctx, ctx.author, member, self.bot)
        await game.start()


    @game.command(description='Lawan musuh-musuh yang ada di Land of Revolution!')
    @app_commands.describe(enemy_tier='Musuh level berapa yang ingin kamu lawan?')
    @app_commands.rename(enemy_tier='level')
    @app_commands.choices(enemy_tier=[
        app_commands.Choice(name='BOSS', value='boss'),
        app_commands.Choice(name='High (Tinggi)', value='high'),
        app_commands.Choice(name="Normal (Sedang)", value='normal'),
        app_commands.Choice(name='Low (Rendah)', value='low')
    ])
    @has_registered()
    @check_blacklist()
    async def battle(self, ctx:commands.Context, enemy_tier:app_commands.Choice[str]): # Choice[value_type]
        """
        Lawan musuh-musuh yang ada di Land of Revolution!
        """
        with open(f'./src/game/enemies/{enemy_tier.value}.json') as file:
            content = file.read()
            enemies = json.loads(content)
        
        enemy = random.choice(enemies)

        game = GameInstance(ctx, ctx.author, enemy, self.bot)
        await game.start()


    @game.command(description='Lihat daftar musuh yang muncul di Land of Revolution!', aliases=['enemy'])
    @has_registered()
    @check_blacklist()
    async def enemies(self, ctx:commands.Context):
        """
        Lihat daftar musuh yang muncul di Land of Revolution!
        """
        view = EnemyView()
        async with ctx.typing():
            await ctx.reply(f"Untuk melihat daftar musuh, silahkan tekan di bawah ini ↓", view=view)


    @game.command(description='Request untuk pemindahan data akun.')
    @app_commands.describe(old_acc = "Akun Discord lamamu atau ID akun Discord lamamu.")
    @app_commands.describe(reason = "Alasan request pemindahan data akun.")
    @app_commands.rename(reason = "alasan")
    @app_commands.rename(old_acc = "akun_lama")
    @has_registered()
    @check_blacklist()
    async def transfer(self, ctx:commands.Context, old_acc:discord.User, *, reason:str):
        """
        Request untuk pemindahan data akun.
        """
        database = connectdb('Game')
        current_acc_data = database.find_one({'_id':ctx.author.id})
        old_acc_data = database.find_one({'_id':old_acc.id})
        if not old_acc_data:
            return await ctx.reply("Akun Land of Revolution tidak ditemukan!\nJika tidak yakin dengan ID akun Discord lamamu, silahkan hubungi langsung Schryzon#4302!")
        
        if ctx.author.id == old_acc_data['_id']:
            return await ctx.reply("Hey! Akun yang kamu cantumkan sama dengan akun Discordmu saat ini!")
        
        embed = discord.Embed(title="Request Transfer Data Akun", color=ctx.author.color, timestamp=ctx.message.created_at)
        embed.add_field(
            name="Akun Lama",
            value=f"Nama: {old_acc_data['name']}\nID: {old_acc_data['_id']}",
            inline=False
        )

        embed.add_field(
            name="Akun Baru",
            value=f"Nama: {current_acc_data['name']}\nID: {current_acc_data['_id']}",
            inline=False
        )

        embed.add_field(
            name="Alasan",
            value=reason,
            inline=False
        )

        embed.set_author(name=ctx.author)
        embed.set_footer(text="Reply \"Approve\" jika disetujui\nReply \"Decline\" jika tidak disetujui")
        channel = self.bot.get_channel(1115422709585817710)
        await channel.send(embed=embed)
        await ctx.send("Aku telah mengirimkan request transfer data akun ke developer!\nMohon ditunggu persetujuannya ya!")

async def setup(bot):
    await bot.add_cog(Game(bot))