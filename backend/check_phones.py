from accounts.models import TechnicianProfile

phones = ['15801608115', '18101158215', '13601133215', '17701280622']

for phone in phones:
    profile = TechnicianProfile.objects.filter(phone=phone).first()
    if profile:
        print(f'手机号 {phone}: 存在，状态: {profile.verification_status}, 用户: {profile.user.username}')
    else:
        print(f'手机号 {phone}: 不存在')
