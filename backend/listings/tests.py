from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User

from accounts.models import TechnicianProfile
from catalog.models import Category
from listings.models import Listing


class PublicCategoryTreeViewTest(TestCase):
    """测试分类树视图"""

    def setUp(self):
        self.client = APIClient()
        # 创建测试分类
        self.root_category = Category.objects.create(
            name="测试分类1",
            status=Category.Status.ENABLED,
            sort_order=1
        )
        self.child_category = Category.objects.create(
            name="测试分类2",
            parent_id=self.root_category.id,
            status=Category.Status.ENABLED,
            sort_order=1
        )

    def test_get_category_tree(self):
        """测试获取分类树"""
        url = reverse('public_category_tree')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tree', response.data)
        tree = response.data['tree']
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['name'], "测试分类1")
        self.assertEqual(len(tree[0]['children']), 1)
        self.assertEqual(tree[0]['children'][0]['name'], "测试分类2")

    @override_settings(PUBLIC_CATEGORY_TREE_CACHE_SECONDS=0)
    def test_category_tree_disables_http_cache_when_seconds_zero(self):
        url = reverse("public_category_tree")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cc = response.get("Cache-Control", "")
        self.assertIn("no-store", cc.lower())
        self.assertIn("no-cache", cc.lower())


class PublicListingsViewTest(TestCase):
    """测试列表视图"""

    def setUp(self):
        self.client = APIClient()
        # 创建测试分类
        self.category = Category.objects.create(
            name="测试分类",
            status=Category.Status.ENABLED,
            sort_order=1
        )
        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        )
        # 创建测试技师
        self.technician = TechnicianProfile.objects.create(
            user=self.user,
            real_name="测试技师",
            phone="13800138000",
            gender="male",
            work_years=5,
            service_types="清洁,维修",
            verification_status=TechnicianProfile.VerificationStatus.APPROVED,
            is_disabled=False
        )
        # 创建测试列表
        self.listing = Listing.objects.create(
            title="测试服务",
            category=self.category,
            technician=self.technician,
            listing_price=100,
            description="测试服务描述",
            status=Listing.Status.PUBLISHED
        )

    def test_get_listings(self):
        """测试获取列表"""
        url = reverse('public_listings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "测试服务")

    def test_get_listings_with_category(self):
        """测试按分类获取列表"""
        url = reverse('public_listings') + f"?category_id={self.category.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        results = response.data['results']
        self.assertEqual(len(results), 1)


class PublicTechniciansViewTest(TestCase):
    """测试技师列表视图"""

    def setUp(self):
        self.client = APIClient()
        # 创建测试用户
        self.user1 = User.objects.create_user(
            username="testuser1",
            password="testpass"
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            password="testpass"
        )
        # 创建测试技师
        self.technician1 = TechnicianProfile.objects.create(
            user=self.user1,
            real_name="测试技师1",
            phone="13800138000",
            gender="male",
            work_years=5,
            service_types="清洁,维修",
            verification_status=TechnicianProfile.VerificationStatus.APPROVED,
            is_disabled=False
        )
        self.technician2 = TechnicianProfile.objects.create(
            user=self.user2,
            real_name="测试技师2",
            phone="13900139000",
            gender="female",
            work_years=3,
            service_types="护理",
            verification_status=TechnicianProfile.VerificationStatus.APPROVED,
            is_disabled=False
        )

    def test_get_technicians(self):
        """测试获取技师列表"""
        url = reverse('public_technicians')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        results = response.data['results']
        self.assertEqual(len(results), 2)

    def test_get_recommended_technicians(self):
        """测试获取推荐技师"""
        # 设置一个技师为推荐
        self.technician1.is_recommended = True
        self.technician1.save()
        
        url = reverse('public_technicians') + "?is_recommended=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['real_name'], "测试技师1")


class PublicListingDetailViewTest(TestCase):
    """测试详情视图"""

    def setUp(self):
        self.client = APIClient()
        # 创建测试分类
        self.category = Category.objects.create(
            name="测试分类",
            status=Category.Status.ENABLED,
            sort_order=1
        )
        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        )
        # 创建测试技师
        self.technician = TechnicianProfile.objects.create(
            user=self.user,
            real_name="测试技师",
            phone="13800138000",
            gender="male",
            work_years=5,
            service_types="清洁,维修",
            verification_status=TechnicianProfile.VerificationStatus.APPROVED,
            is_disabled=False
        )
        # 创建测试列表
        self.listing = Listing.objects.create(
            title="测试服务",
            category=self.category,
            technician=self.technician,
            listing_price=100,
            description="测试服务描述",
            status=Listing.Status.PUBLISHED
        )

    def test_get_listing_detail(self):
        """测试获取详情"""
        url = reverse('public_listing_detail', kwargs={'listing_id': self.listing.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "测试服务")
        self.assertEqual(response.data['listing_price'], '100.00')

