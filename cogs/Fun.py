import asyncio
from os import remove
import random
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image
from io import BytesIO
from scripts.main import check_blacklist, has_voted

class Fun(commands.Cog):
    """
    Command khusus untuk bersenang-senang
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=['tebak'], description='Ayo main tebak angka bersamaku!')
    @has_voted()
    @check_blacklist()
    async def guess(self, ctx:commands.Context):
        """
        Ayo main tebak angka bersamaku!
        """
        count = 5
        hints = 3
        number = random.randint(1, 20)
        num_store = None
        await ctx.send(":grey_exclamation: **Kamu harus menebak angka yang aku pikirkan dari `1-20`!**")
        await asyncio.sleep(2.5)
        while count != 0:
            if count < 5 and count != 1:
                await ctx.send(f"**Kamu punya `{count}` attempt. Ketik `hint` jika butuh bantuan.\nHint tersisa: `{hints}` | Akhiri game dengan mengetik `end`.**")
            elif count == 1:
                await ctx.send(f"**Kamu punya `{count}` attempt tersisa!\nHint tersisa: `{hints}` | Akhiri game dengan mengetik `end`.**")
            else:
                await ctx.send(f"**Kamu punya `{count}` attempt, ayo coba tebak angka yang kupilih!\nAkhiri game dengan mengetik `end`.**")
            try:
                r1 = await self.bot.wait_for('message', check = lambda r: r.author == ctx.author and r.channel == ctx.channel, timeout = 20.0)

            except asyncio.TimeoutError:
                await ctx.channel.send(f"**Yah, dikacangin dong :(**")
                return
            
            if r1.content == str(number):
                await ctx.channel.send(f"**Tepat sekali, angkanya yaitu `{number}`!**")
                return
            
            elif r1.content.isdigit() == False and r1.content.lower() != "hint" and r1.content.lower() != "end" and r1.content.lower() != "end.":
                await ctx.channel.send(f":negative_squared_cross_mark: **Hey, kamu hanya bisa menjawab dengan angka bilangan bulat saja!**", delete_after=2.0)
                await asyncio.sleep(1.5)

            elif r1.content.lower() == "end" or r1.content.lower() == "end.":
                await ctx.channel.send(":no_entry: **Game diakhiri.**")
                return
            
            elif r1.content.lower() == "hint":
                if num_store == None:
                    await ctx.channel.send(":negative_squared_cross_mark: **Kamu belum ada menebak, tebak dulu baru bisa dikasi hint!**", delete_after=2.0)
                    await asyncio.sleep(1.5)

                elif hints == 0:
                    await ctx.channel.send(":negative_squared_cross_mark: **Kamu kehabisan hint!**", delete_after=2.0)
                    await asyncio.sleep(1.5)

                elif number > num_store:
                    await ctx.channel.send(f":grey_question: Hint: **Angka terakhirmu, `{num_store}` lebih kecil dari yang kupilih.**", delete_after=2.5)
                    hints -= 1
                    await asyncio.sleep(2.0)

                elif number < num_store:
                    await ctx.channel.send(f":grey_question: Hint: **Angka terakhirmu, `{num_store}` lebih besar dari yang kupilih.**", delete_after=2.5)
                    hints -= 1
                    await asyncio.sleep(2.0)
            else:
                if int(r1.content) > 20:
                    await ctx.channel.send(f":negative_squared_cross_mark: **Angkamu lebih tinggi dari 20!**", delete_after=2.0)
                    await asyncio.sleep(1.5)

                else:
                    count -= 1
                    await ctx.channel.send(f":x: **Salah!**")
                    num_store = int(r1.content)
                    await asyncio.sleep(1.5)
                    
        if count == 0:
            await ctx.send(f":exclamation: **Kamu kehabisan attempt!\nAngka yang kupilih yaitu `{number}`!**")
            
    
    @commands.hybrid_command(aliases=['jodohkan', 'jodoh'], description="Jodohkan seseorang denganmu atau orang lain!")
    @app_commands.rename(member1='pengguna_1', member2='pengguna_2')
    @app_commands.describe(member1='Siapa yang nembak nih?')
    @app_commands.describe(member2='Siapa pasangannya?')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_voted()
    @check_blacklist()
    async def ship(self, ctx:commands.Context, member1: discord.Member, member2:discord.Member):
        """
        Jodohkan seorang teman atau orang lain dengan pengguna lainnya!
        """
        if member1 == ctx.author and member2==ctx.author:
            await ctx.send("Aku tidak bisa menjodohkanmu dengan dirimu sendiri! TwT")
            return
        
        success = random.randint(1, 100)
        success_ranges = [
            (100, f"__Match made in Heaven!__\n{member1.name} dan {member2.name} akan menjadi pasangan terbaik! ❤️", "./src/ships/ship.png"),
            (90, f"It's __true love!__\n{member1.name} sangat cocok berpasangan dengan {member2.name}! ❤️", "./src/ships/ship.png"),
            (80, f"__Lovey, dovey!__\n{member1.name} dan {member2.name} akan menjalin hubungan yang dekat! ❤️", "./src/ships/ship.png"),
            (70, f"__Besties for life!__\n{member1.name} akan menjadi sahabat setia untuk {member2.name}! <:hug:1084251318073438289>", "./src/ships/fship.png"),
            (50, f"__They somehow fit together.__\n{member1.name} cocok menjadi temannya {member2.name}. 👍", "./src/ships/gship.png"),
            (25, f"__Not good!__\n{member1.name} dan {member2.name} tidak akan berbahagia saat berpasangan. 👎", "./src/ships/bship.png"),
            (0, f"__This is bad!__\n{member1.name} dan {member2.name} merupakan pasangan yang tidak cocok! 💔", "./src/ships/shship.png")
        ]

        # Find the appropriate success message and image based on the success value
        for success_range, message, image_path in success_ranges:
            if success >= success_range:
                ss = message
                sus = Image.open(image_path)
                break

        asset1 = member1.display_avatar.with_format('png').with_size(128)
        asset2 = member2.display_avatar.with_format('png').with_size(128)
        data1 = BytesIO(await asset1.read())
        data2 = BytesIO(await asset2.read())
        pfp1 = Image.open(data1)
        pfp1 = pfp1.resize((420, 420))
        sus.paste(pfp1, (90, 28))
        pfp2 = Image.open(data2)
        pfp2 = pfp2.resize((420, 420))
        sus.paste(pfp2, (1024, 28))
        sus.save('shipres.png')

        L = len(member1.name)//2
        LL = len(member2.name)//2
        embed = discord.Embed(title="Hasil Penjodohan", description = f"❤️ **{success}%** ❤️\n{ss}\n**Nama ship:** {member1.name[:L] + member2.name[LL:]}", color=ctx.author.colour)
        embed.set_footer(text=f"{member1.name} dan {member2.name}")
        file = discord.File("shipres.png")
        embed.set_image(url= "attachment://shipres.png")
        await ctx.send(file = file, embed = embed)
        remove('./shipres.png')

async def setup (bot):
    await bot.add_cog(Fun(bot))