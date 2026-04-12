import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

# 要删除的用户名列表
usernames = ['similie', 'lihaoa', '用户_82154', 'wendy']

# 遍历删除每个用户
for username in usernames:
    try:
        user = User.objects.get(username=username)
        user.delete()
        print(f'删除用户 {username} 成功')
    except User.DoesNotExist:
        print(f'用户 {username} 不存在')

# 确认删除结果
remaining_users = User.objects.count()
print(f'删除完成，剩余用户数量: {remaining_users}')
