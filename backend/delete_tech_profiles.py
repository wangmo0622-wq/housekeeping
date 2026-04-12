import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import TechnicianProfile

# 要删除的手机号列表
phones = ['15801608115', '18101158215', '13601133215', '17701280622']

# 遍历删除每个手机号对应的技师认证数据
for phone in phones:
    profile = TechnicianProfile.objects.filter(phone=phone).first()
    if profile:
        profile.delete()
        print(f'删除手机号 {phone} 的技师认证数据')
    else:
        print(f'手机号 {phone} 的技师认证数据不存在')

# 确认删除结果
remaining_profiles = TechnicianProfile.objects.count()
print(f'删除完成，剩余技师认证数据数量: {remaining_profiles}')
