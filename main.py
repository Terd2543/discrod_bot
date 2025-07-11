import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed, ui, SlashOption
import logging
import re
import os
import requests
import json
import time
import config
import datetime
import asyncio

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# /// config.py กำหนดในนี้

admin_log = config.admin_log
ownerid = config.ownerid
log_top = config.log_top
log_role2 = config.log_role
log_embed = config.log_embed
phone = config.phone
APIKEY = config.APIKEY
iamge = config.image


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

@bot.event
async def on_ready():
    os.system('cls' if os.name == 'nt' else 'clear')  # ล้างหน้าจอ
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

    print(Colors.OKCYAN + f"""
╔════════════════════════════════════════════════════╗
║           Jared SHOP V.2 ระบบพร้อมใช้งาน         ║
╠════════════════════════════════════════════════════╣
║  ชื่อบอท       : {bot.user.name:<35}║
║  ไอดีบอท       : {bot.user.id:<35}║
║  เวลา           : {current_time:<35}║
║                                                    ║
║  ลิขสิทธิ์      : icewen_2                         ║
║  Copyright    : © 2025 icewen_2 All Rights Reserved║
╚════════════════════════════════════════════════════╝
""" + Colors.ENDC)
    bot.add_view(MainView())

#[##]]##]#]#]#]#]#]#]#]##]#]#]#[#[##[#]]]


@bot.slash_command(name="add-role", description="เพิ่มยศใหม่ในระบบ")
async def add_role2(
    interaction: nextcord.Interaction,
    name: str = nextcord.SlashOption(name="name", description="ชื่อของยศ"),
    description: str = nextcord.SlashOption(name="description", description="คำอธิบายของยศ"),
    price: int = nextcord.SlashOption(name="price", description="ราคาของยศ"),
    role: nextcord.Role = nextcord.SlashOption(name="role", description="เลือกยศที่ต้องการเพิ่ม"),
    emoji: str = nextcord.SlashOption(name="emoji", description="เลือก emoji ที่จะใช้สำหรับยศ")
):
    if interaction.user.id not in ownerid:
        await interaction.response.send_message("```❌ คุณไม่มีสิทธิ์ใช้งานคำสั่งนี้```")
        return
    
    try:
        with open('./BOT/role.json', 'r') as f:
            roles_data = json.load(f)
        
        role_key = f"role{len(roles_data) + 1}"

        roles_data[role_key] = {
            "name": name,
            "description": description,
            "price": price,
            "roleId": role.id,
            "emoji": emoji
        }

        
        with open('./BOT/role.json', 'w') as f:
            json.dump(roles_data, f, indent=4)

        
        await interaction.response.send_message(
            f">>> ✅ ยศ `{name}` ถูกเพิ่มลงในระบบแล้ว!\n\n- **ชื่อยศ**: `{name}`\n- **คำอธิบาย**: `{description}`\n- **ราคา**: `{price} point`\n- **ยศ**: {role.mention}\n- **Emoji**: {emoji}",
            ephemeral=True
        )
        await update_embed()
    
    except FileNotFoundError:
        
        roles_data = {
            "role1": {
                "name": name,
                "description": description,
                "price": price,
                "roleId": role.id,
                "emoji": emoji
            }
        }

        with open('./BOT/role.json', 'w') as f:
            json.dump(roles_data, f, indent=4)

        await interaction.response.send_message(
            f">>> ✅ ยศ `{name}` ถูกเพิ่มลงในระบบแล้ว (ไฟล์ยังไม่ได้ถูกสร้าง)",
            ephemeral=True
        )


##[#[#[##[#[#]#[#[#]#[##[#[#[#[#[]]]]]]]]]]]

def load_user_data():
    try:
        with open("BOT/users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_data(data):
    with open("BOT/users.json", "w") as f:
        json.dump(data, f, indent=4)

def update_balance(user_id, amount):
    data = load_user_data()
    if str(user_id) not in data:
        data[str(user_id)] = {"point": 0, "allpoint": 0}
    data[str(user_id)]["point"] += amount
    if amount > 0:
        data[str(user_id)]["allpoint"] += amount
    save_user_data(data)

# Log หลักเลยอันนี้ ของเติมเงิน แอดมิน
async def send_log_embed(user, admin, amount, action):
    log_channel = bot.get_channel(admin_log)
    if log_channel:
        embed = nextcord.Embed(title="• 🏛️ ระบบจัดการยอดเงิน", color=nextcord.Color.blurple())
        embed.add_field(name="`• 👤 ผู้ใช้`", value=f"{user.mention} ({user.id})", inline=False)
        embed.add_field(name="`• 🏛️ จำนวนเงิน", value=f"`{'+' if action == 'เพิ่ม' else '-'}{amount}` บาทท", inline=False)
        embed.add_field(name="`• 🔄 ระบบเติม`", value=f"`{action}ผ่านแอดมิน`", inline=False)
        embed.add_field(name="`• 👑 ผู้ทำรายการ`", value=f"{admin.mention} ({admin.id})", inline=False)
        embed.set_footer(text="ระบบจัดการ เงินผู้ใช้ครับบ")
        await log_channel.send(embed=embed)


class AddMoneyModal(ui.Modal):
    def __init__(self):
        super().__init__("💸 เพิ่มเงิน")
        self.user_id_input = ui.TextInput(label="ID ผู้ใช้", min_length=18, max_length=20)
        self.amount_input = ui.TextInput(label="จำนวนเงิน", placeholder="กรอกจำนวนเงิน")
        self.confirm_input = ui.TextInput(label="พิมพ์ yes หรือ no", placeholder="ยืนยันการทำรายการ")
        self.add_item(self.user_id_input)
        self.add_item(self.amount_input)
        self.add_item(self.confirm_input)

    async def callback(self, interaction: Interaction):
        if self.confirm_input.value.lower() == "yes":
            user_id = int(self.user_id_input.value)
            amount = int(self.amount_input.value)
            user = interaction.guild.get_member(user_id)
            if user:
                update_balance(user.id, amount)
                await send_log_embed(user, interaction.user, amount, "เพิ่ม")
                await interaction.response.send_message("### > 🏛️ = เพิ่มเงินสำเร็จ", ephemeral=True)
            else:
                await interaction.response.send_message("### ไม่พบผู้ใช้", ephemeral=True)
        else:
            await interaction.response.send_message("### ยกเลิกการทำรายการสำเร็จ", ephemeral=True)


class RemoveMoneyModal(ui.Modal):
    def __init__(self):
        super().__init__("🗑️ ลบเงิน")
        self.user_id_input = ui.TextInput(label="ID ผู้ใช้", min_length=18, max_length=20)
        self.amount_input = ui.TextInput(label="จำนวนเงิน", placeholder="กรอกจำนวนเงิน")
        self.confirm_input = ui.TextInput(label="พิมพ์ yes หรือ no", placeholder="ยืนยันการทำรายการ")
        self.add_item(self.user_id_input)
        self.add_item(self.amount_input)
        self.add_item(self.confirm_input)

    async def callback(self, interaction: Interaction):
        if self.confirm_input.value.lower() == "yes":
            user_id = int(self.user_id_input.value)
            amount = int(self.amount_input.value)
            user = interaction.guild.get_member(user_id)
            if user:
                update_balance(user.id, -amount)
                await send_log_embed(user, interaction.user, amount, "ลบ")
                await interaction.response.send_message("### > ⚠️ ลบเงินสำเร็จ!", ephemeral=True)
            else:
                await interaction.response.send_message("### ไม่พบผู้ใช้", ephemeral=True)
        else:
            await interaction.response.send_message("### ยกเลิกการทำรายการแล้ว", ephemeral=True)


class CheckMoneyModal(ui.Modal):
    def __init__(self):
        super().__init__("🌵 เช็คยอดเงิน")
        self.user_id_input = ui.TextInput(label="ID ผู้ใช้", min_length=18, max_length=20)
        self.add_item(self.user_id_input)

    async def callback(self, interaction: Interaction):
        user_id = int(self.user_id_input.value)
        data = load_user_data()
        user_data = data.get(str(user_id), {"point": 0, "allpoint": 0})
        embed = nextcord.Embed(title="💰 ยอดเงินผู้ใช้", color=nextcord.Color.blurple())
        embed.add_field(name="`• 👤 ผู้ใช้`", value=f"<@{user_id}>", inline=False)
        embed.add_field(name="`• 🏛️ เงิน ปัจจุบัน`", value=f"`{user_data['point']}` บาทท", inline=False)
        embed.add_field(name="`• 🍇 ยอดเติมทั้งหมด`", value=f"`{user_data['allpoint']}` บาทท", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)




        


##[#[##[#[#]#[##[#]#[#[##[#[#[]]]]]]]]]

class PointView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label="꒰💸 เพิ่มเงิน ꒱", style=nextcord.ButtonStyle.green)
    async def add_points(self, button: nextcord.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(AddMoneyModal())

    @nextcord.ui.button(label="꒰🗑️ ลบเงิน ꒱", style=nextcord.ButtonStyle.red)
    async def remove_points(self, button: nextcord.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(RemoveMoneyModal())

    @nextcord.ui.button(label="꒰🌵 เช็คยอดเงิน ꒱", style=nextcord.ButtonStyle.blurple)
    async def check_points(self, button: nextcord.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(CheckMoneyModal())

@bot.slash_command(name="add-point", description="🥐 จัดการ เงิน ผู้ใช้(ทุกคนครับบ)")
async def add_point(interaction: nextcord.Interaction):
    if interaction.user.id not in ownerid:
        await interaction.response.send_message("คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return

    
    embed = nextcord.Embed(description="### 🏛️ • เมนูจัดการเกี่ยวกับเงินทุกคนในเซิฟเวอร์", color=nextcord.Color.blurple())
    view = PointView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)









###[#[#[##[#]#]%]#]%]#]#]#]#


def load_json(file):
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


class top(nextcord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title='เติมเงินซองอั๋งเปา', timeout=None, custom_id='topup-modal')
        self.bot = bot
        self.a = nextcord.ui.TextInput(
            label='ลิ้งค์ซองอั่งเปา',
            placeholder='https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx',
            style=nextcord.TextInputStyle.short,
            required=True
        )
        self.add_item(self.a)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            link = str(self.a.value).strip()

            # ตรวจสอบว่าลิงก์ถูกต้องหรือไม่
            if not re.match(r'https:\/\/gift\.truemoney\.com\/campaign\/\?v=[a-zA-Z0-9]{18}', link):
                await interaction.followup.send(
                    embed=nextcord.Embed(
                        description="### ❌ ลิ้งค์อั่งเปาไม่ถูกต้อง",
                        color=nextcord.Color.red()
                    ),
                    ephemeral=True
                )
                return

            payload = {
                "keyapi": APIKEY,
                "phone": phone,
                "gift_link": link
            }
            r = requests.post("https://www.planariashop.com/api/truewallet.php", json=payload)
            response = r.json()

            # ตรวจสอบสถานะการเติมเงิน
            if response.get('status') == "error":
                await interaction.followup.send(
                    embed=nextcord.Embed(
                        description=f"### ❌ เติมเงินไม่สำเร็จ {response.get('message')}",
                        color=nextcord.Color.red()
                    ),
                    ephemeral=True
                )
                return

            # แปลงค่า amount เป็น float
            amount = float(response.get('amount', 0))

            user_data = load_json('./BOT/users.json')
            user_id = str(interaction.user.id)

            if user_id in user_data:
                user_data[user_id]['point'] += amount
                user_data[user_id]['allpoint'] += amount
            else:
                user_data[user_id] = {
                    "userId": int(user_id),
                    "point": amount,
                    "allpoint": amount
                }

            save_json('./BOT/users.json', user_data)

            embed = nextcord.Embed(
                description=f'✅ เติมเงินสำเร็จ `{amount}` บาท',
                color=nextcord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            log_embed = nextcord.Embed(
    title="**__꒰ 🔔 ꒱ เติมเงินสำเร็จ__**",
    color=nextcord.Color.blurple()
)
            log_embed.add_field(name="`👤 : ผู้ใช้`", value=interaction.user.mention, inline=False)
            log_embed.add_field(name="`✅ : สถานะ`", value="`เติมสำเร็จแล้ว`", inline=False)
            log_embed.add_field(name="`🧧 : ระบบ`", value="`ซองอั่งเปา`", inline=False)
            log_embed.add_field(name="`🔔 : จำนวนเงิน`", value=f"``{amount}`` บาท", inline=False)
            log_embed.add_field(name="`🧷 : ลิ้ง`", value=f"[กดที่นี่]({link})", inline=False)
            avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
            log_embed.set_thumbnail(url=avatar_url)
            log_embed.set_footer(text="ICEWEN_2 : log", icon_url="https://cdn.discordapp.com/attachments/1347632960244940841/1357641155478683758/IMG_3789.gif?ex=67f0f15b&is=67ef9fdb&hm=491f6d19ba4ce34e54e76250d7743e94d5ad29165250f16e2473f04026fb9632&")
            log_channel = self.bot.get_channel(log_top)
            if log_channel:
                await log_channel.send(embed=log_embed)
            else:
                logging.warning(f"ไม่พบช่อง Log (ID: {log_top})")
        except Exception as e:
            logging.error(f"เกิดข้อผิดพลาด: {e}")
            await interaction.followup.send(
                embed=nextcord.Embed(
                    description="### ❌ เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง",
                    color=nextcord.Color.red()
                ),
                ephemeral=True)



##_#[#[##[#[##[#[##[#[#[##[#]##[#[##[#[#]]]]]]]]]]]]]
class con(nextcord.ui.View):
    def __init__(self, message, value):
        super().__init__()
        self.message = message
        self.value = value

    @nextcord.ui.button(label='ยืนยันสั่งซื้อ', custom_id='already', style=nextcord.ButtonStyle.green)
    async def already(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        try:
            roleJSON = json.load(open('./BOT/role.json', 'r', encoding='utf-8'))
            userJSON = json.load(open('./BOT/users.json', 'r', encoding='utf-8'))

            if userJSON[str(interaction.user.id)]['point'] < roleJSON[self.value]['price']:
                embed = nextcord.Embed(description='```❌ ยอดเงินไม่เพียงพอ```', color=nextcord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            userJSON[str(interaction.user.id)]['point'] -= roleJSON[self.value]['price']
            with open('./BOT/users.json', 'w', encoding='utf-8') as f:
                json.dump(userJSON, f, indent=4, ensure_ascii=False)
            
            role = interaction.guild.get_role(roleJSON[self.value]['roleId'])
            if role:
                await interaction.user.add_roles(role)
            
            embed = nextcord.Embed(
                description=f'**__꒰ 🔔 ꒱ ซื้อยศสำเร็จ__** <@&{role.id}>',
                color=nextcord.Color.blurple()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await update_embed()

            channelLog = interaction.guild.get_channel(log_role2)
            if channelLog:
                log_embed = nextcord.Embed(
                    title='**__꒰ 🎀 ꒱ : แจ้งเตือนการซื้อยศ__**',
                    description=f">>> `👤 : ผู้ใช้`: {interaction.user.mention}\n`💎 : ยศที่ซื้อ`: <@&{role.id}>\n`🏛️ : ราคา`: ```{roleJSON[self.value]['price']} บาท```\n`🔔 ยอดคงเหลือ`: ```{userJSON[str(interaction.user.id)]['point']} บาท```", color=nextcord.Color.blurple())
                log_embed.set_thumbnail(url=interaction.user.avatar.url)
                log_embed.set_footer(text="ICEWEN_2 : LOG", icon_url="https://cdn.discordapp.com/attachments/1347632960244940841/1357641155478683758/IMG_3789.gif?ex=67f0f15b&is=67ef9fdb&hm=491f6d19ba4ce34e54e76250d7743e94d5ad29165250f16e2473f04026fb9632&")
                await channelLog.send(embed=log_embed)

        except Exception as e:
            embed = nextcord.Embed(description=f"```⚠️ ขอโทษค่ะ มีข้อผิดพลาด: {str(e)}```", color=nextcord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.ui.button(label="ยกเลิกสั่งซื้อ", style=nextcord.ButtonStyle.danger, custom_id="cancel_button")
    async def cancel_button(self, button: nextcord.ui.Button, interaction: Interaction):
        await interaction.response.edit_message(content="### ❌ ยกเลิกแล้วครับบบ", embed=None, view=None)

#552525252662626266262673737373):฿&:8282

class RoleSelect(nextcord.ui.Select):
    def __init__(self):
        options = []
        roleJSON = json.load(open('./BOT/role.json', 'r', encoding='utf-8'))
        for role in roleJSON:
            options.append(nextcord.SelectOption(
                label=roleJSON[role]['name'],
                description=f"{roleJSON[role]['description']} | ราคา {roleJSON[role]['price']}",
                value=role,
                emoji=roleJSON[role]['emoji']
            ))
            
        options.append(nextcord.SelectOption(
            label="ล้างตัวเลือกใหม่",
            description="",
            value="รีเซ็ตตัวเลือก",
            emoji="<:pn:1291155295678103565>"
        ))
            
        options = options[:25]
        super().__init__(
            custom_id='select-role',
            placeholder='⌞ 🔔  เลือกยศที่คุณต้องการซื้อ ⌝',
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(self, interaction: nextcord.Interaction):
        if self.values[0] == "รีเซ็ตตัวเลือก":
            await interaction.response.edit_message(view=MainView())
            return
        selected = self.values[0]
        roleJSON = json.load(open('./BOT/role.json', 'r', encoding='utf-8'))
        embed = nextcord.Embed(
    title='**__꒰🔔꒱ รายละเอียดก่อนซื้อ__**',
    color=nextcord.Color.blurple()
        )
        embed.add_field(
            name="**🎀 ยศที่จะได้รับ**",
            value=f"<@&{roleJSON[selected]['roleId']}>", inline=True
        )
        embed.add_field(
            name="**🌟 ราคาของยศ**",
            value=f"```{roleJSON[selected]['price']} บาท```", inline=True
        )
        embed.set_footer(text="ICEWEN_2 : SELL", icon_url="https://cdn.discordapp.com/attachments/1347632960244940841/1357641155478683758/IMG_3789.gif?ex=67f0f15b&is=67ef9fdb&hm=491f6d19ba4ce34e54e76250d7743e94d5ad29165250f16e2473f04026fb9632&")
        await interaction.response.send_message(embed=embed, ephemeral=True, view=con(interaction.message, selected))

# //////////:://:///////////////////
class MainView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect())

    @nextcord.ui.button(label="⌞ 🏛️  เติมเงิน ⌝", style=nextcord.ButtonStyle.primary, row=2, custom_id="top_up")
    async def top_up(self, button: nextcord.ui.Button, interaction: Interaction):
        modal = top(bot)
        await interaction.response.send_modal(modal)

    @nextcord.ui.button(label="⌞ 💵  เช็คยอดเงิน ⌝", style=nextcord.ButtonStyle.primary, row=2, custom_id="check_balance")
    async def check_balance(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        users_data = load_json('BOT/users.json')
        point = users_data.get(str(interaction.user.id), {}).get('point', 0)

        embed = nextcord.Embed(
            title="**__꒰ 🏛️ ꒱ ยอดเงินคงเหลือของคุณ__**",
            description=f"คุณมียอดเงินคงเหลือทั้งหมด\n\n> **`{point:,.2f}`** บาท",
            color=nextcord.Color.blurple()
        )
        embed.set_thumbnail(
            url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        )
        embed.set_footer(
            text=f"ผู้ใช้งาน: {interaction.user.name}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @nextcord.ui.button(label="⌞ 🔁 โอนบทบาท ⌝", style=nextcord.ButtonStyle.green, row=2, custom_id="transfer_role")
    async def transfer_role(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message(view=Select2(), ephemeral=True)





# /:/:////////////////////////


class Select2(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        roleJSON = json.load(open('./BOT/role.json', 'r', encoding='utf-8'))

        options = []
        for role in roleJSON:
            options.append(nextcord.SelectOption(
                label=roleJSON[role]['name'],
                description=f"{roleJSON[role]['description']} | ราคา {roleJSON[role]['price']}",
                value=role,
                emoji=roleJSON[role]['emoji']
            ))

        self.add_item(SelectRoleDropdown(options))

class SelectRoleDropdown(nextcord.ui.Select):
    def __init__(self, options):
        super().__init__(
            placeholder="⌞ 🎀 เลือกยศที่คุณต้องการโอน ⌝",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="SELECT"
        )

    async def callback(self, interaction: nextcord.Interaction):
        selected = self.values[0]
        embed = nextcord.Embed(
            title="**__꒰ 📒 ꒱ รายละเอียดการโอนยศ__**",
            description=f"```จะได้รับยศทันทีเมื่อโอนสำเร็จแล้ว```",
            color=nextcord.Color.blue()
        )
        embed.add_field(
            name="**🎀 ยศที่จะได้รับ**",
            value=f"<@&{json.load(open('./BOT/role.json'))[selected]['roleId']}>", inline=False
        )
        embed.add_field(
            name="**🌟 ราคาของยศ**",
            value=f"```{json.load(open('./BOT/role.json'))[selected]['price']} บาท```", inline=False
        )
        embed.set_footer(text="ICEWEN_2 : SELL", icon_url="https://cdn.discordapp.com/attachments/1347632960244940841/1357641155478683758/IMG_3789.gif?ex=67f0f15b&is=67ef9fdb&hm=491f6d19ba4ce34e54e76250d7743e94d5ad29165250f16e2473f04026fb9632&")

        view = Conrole(selected)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ////;(/;//((/(/(/(/(/())))))))



class Conrole(nextcord.ui.View):
    def __init__(self, selected_role):
        super().__init__(timeout=None)
        self.selected_role = selected_role

    @nextcord.ui.button(label="ยืนยันการโอน", style=nextcord.ButtonStyle.success)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(ROLE(self.selected_role))

    @nextcord.ui.button(label="ยกเลิกการโอน", style=nextcord.ButtonStyle.danger)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.edit_message(content="```❌ ยกเลิกการโอนยศเรียบร้อย```", embed=None, view=None)



class ROLE(nextcord.ui.Modal):
    def __init__(self, selected_role):
        super().__init__("กรอกไอดีผู้รับ")
        self.selected_role = selected_role

        self.receiver_id = nextcord.ui.TextInput(
            label="กรุณาใส่ User ID ผู้รับ",
            placeholder="เช่น 123456789012345678",
            required=True,
        )
        self.add_item(self.receiver_id)

    async def callback(self, interaction: nextcord.Interaction):
        guild = interaction.guild
        sender = interaction.user
        receiver_id = self.receiver_id.value
        role_data = json.load(open('./BOT/role.json', 'r', encoding='utf-8'))[self.selected_role]

        try:
            receiver = await guild.fetch_member(int(receiver_id))
        except:
            await interaction.response.send_message("### ❌ ไม่พบผู้ใช้ในเซิร์ฟเวอร์นะคะพี่", ephemeral=True)
            return

        role = guild.get_role(int(role_data["roleId"]))
        if role in sender.roles:
            await sender.remove_roles(role, reason="โอนบทบาทให้ผู้อื่น")
            await receiver.add_roles(role, reason="ได้รับบทบาทจากการโอน")
        else:
            c_embed = nextcord.Embed(description=" ```❌นายไม่มียศนี้นะโอนไม่ได้```", color=nextcord.Color.red())
            await interaction.response.send_message("คุณไม่มีบทบาทนี้", ephemeral=True)
            return

        log_channel = guild.get_channel(log_role2)
        embed = nextcord.Embed(
            title="**__꒰ ❇️ ꒱ : ระบบโอนบทบาท__**",
            description=f"`🤴🏻 ผู้โอน`: {sender.mention}\n`🙋‍ ผู้รับ`: {receiver.mention}\n`💎 ยศที่ได้รับ`: <@&{role.id}>\n`⏰ เวลา`: <t:{int(datetime.datetime.now().timestamp())}:F>",
            color=nextcord.Color.blue()
        )
        embed.set_footer(text="ICEWEN_2 : SELL", icon_url="https://cdn.discordapp.com/attachments/1347632960244940841/1357641155478683758/IMG_3789.gif?ex=67f0f15b&is=67ef9fdb&hm=491f6d19ba4ce34e54e76250d7743e94d5ad29165250f16e2473f04026fb9632&")
        await log_channel.send(embed=embed)

        s_embed = nextcord.Embed(description="```✅โอนบทบาทเรียบร้อยแล้ว```", color=nextcord.Color.green())
        await interaction.response.send_message(embed=s_embed, ephemeral=True)





# ////////////////////////:/:

async def update_embed():
    channel = bot.get_channel(log_embed)
    if not channel:
        return
    async for message in channel.history(limit=1):
        if message.author == bot.user and message.embeds:
            embed = nextcord.Embed(
                title="**꒰ 🔔 ꒱ ระบบซื้อบทบาท [ 24 ชั่วโมง ]**", 
                description=(
                    "```୨୧ ==== รายละเอียดต่างๆ ==== ୨୧\n"
                    "ꔫ・ 🔔 ซื้อยศผ่านบอทได้เลย ซื้อแล้วได้ยศทันที\n"
                    "ꔫ・ 🧧 เติมเงินง่ายๆเพื่อเปิดบัญชี\n"
                    "ꔫ・ 🏛️ สามารถโอนบทบาทได้ และ ซื้อยศให้คนอื่นได้\n\n"
                    "                                 ```"
                )
            )
            embed.set_footer(
                text=f"ICEWEN_2 : {message.guild.name}", 
                icon_url="https://cdn.discordapp.com/attachments/1347632960244940841/1357641155478683758/IMG_3789.gif"
            )
            embed.set_image(url=iamge)

            await message.edit(embed=embed, view=MainView())
            break








@bot.slash_command(name="setup-role", description="🏛️ ติดตั้งระบบซื้อยศ24ชม")
async def setup(interaction: nextcord.Interaction):
    if interaction.user.id not in ownerid:
        await interaction.response.send_message("```❌ คุณไม่มีสิทธิ์ใช้งานคำสั่งนี้```")
        return
    
    embed = nextcord.Embed(description="```🔄 กำลังติดตั้งขายยศ```")
    await interaction.response.send_message('``` ติดตั้งสำเร็จ ✅```', ephemeral=True)
    await interaction.channel.send(embed=embed)
    await update_embed()

bot.run(config.TOKEN)