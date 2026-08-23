from django.test import TestCase, Client
from django.contrib.auth.models import User
from spices.models import Category, Product, ProductVariant, CartItem, UserProfile, Order, OrderItem

class CartAndCheckoutTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', first_name='John', last_name='Doe', email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password123')
        
        self.category = Category.objects.create(name='Spices', slug='spices')
        self.product = Product.objects.create(name='Cardamom Powder', slug='cardamom-powder', category=self.category)
        self.variant1 = ProductVariant.objects.create(product=self.product, weight='50g', price=150.00, is_default=True)
        self.variant2 = ProductVariant.objects.create(product=self.product, weight='100g', price=280.00)

    def test_anonymous_add_to_cart_succeeds_in_session(self):
        client = Client()
        response = client.post('/api/cart/add/', data={'variant_id': self.variant1.id, 'quantity': 1}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('cart_count'), 1)
        
        # Verify anonymous cart view renders items
        res_cart = client.get('/cart/')
        self.assertEqual(res_cart.status_code, 200)
        self.assertEqual(len(res_cart.context['cart_items']), 1)
        self.assertEqual(res_cart.context['subtotal'], 150.0)

    def test_authenticated_add_to_cart_success(self):
        client = Client()
        client.force_login(self.user1)
        response = client.post('/api/cart/add/', data={'variant_id': self.variant1.id, 'quantity': 2}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('cart_count'), 2)
        
        # Verify DB
        cart_item = CartItem.objects.get(user=self.user1, variant=self.variant1)
        self.assertEqual(cart_item.quantity, 2)

    def test_user_cart_isolation(self):
        CartItem.objects.create(user=self.user1, variant=self.variant1, quantity=2)
        CartItem.objects.create(user=self.user2, variant=self.variant2, quantity=5)

        client1 = Client()
        client1.force_login(self.user1)
        res1 = client1.get('/cart/')
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(len(res1.context['cart_items']), 1)
        self.assertEqual(res1.context['cart_items'][0]['variant_id'], self.variant1.id)
        self.assertEqual(res1.context['subtotal'], 300.0)

        client2 = Client()
        client2.force_login(self.user2)
        res2 = client2.get('/cart/')
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(len(res2.context['cart_items']), 1)
        self.assertEqual(res2.context['cart_items'][0]['variant_id'], self.variant2.id)
        self.assertEqual(res2.context['subtotal'], 1400.0)

    def test_update_and_remove_cart(self):
        client = Client()
        client.force_login(self.user1)
        
        client.post('/api/cart/add/', data={'variant_id': self.variant1.id, 'quantity': 1}, content_type='application/json')
        
        res_update = client.post('/api/cart/update/', data={'variant_id': self.variant1.id, 'quantity': 3}, content_type='application/json')
        self.assertEqual(res_update.json()['cart_count'], 3)
        self.assertEqual(res_update.json()['subtotal'], 450.0)

        res_remove = client.post('/api/cart/remove/', data={'variant_id': self.variant1.id}, content_type='application/json')
        self.assertEqual(res_remove.json()['cart_count'], 0)
        self.assertFalse(CartItem.objects.filter(user=self.user1, variant=self.variant1).exists())

    def test_incomplete_profile_blocks_checkout(self):
        client = Client()
        client.force_login(self.user2)
        
        CartItem.objects.create(user=self.user2, variant=self.variant1, quantity=1)
        
        res = client.post('/checkout/', data={
            'first_name': '',
            'phone': ''
        }, content_type='application/json')
        
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertTrue(data.get('profile_incomplete'))

    def test_complete_profile_allows_checkout(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user1)
        profile.phone = '9876543210'
        profile.address = '123 Main St'
        profile.state = 'Kerala'
        profile.district = 'Idukki'
        profile.pincode = '685551'
        profile.save()

        self.assertTrue(profile.is_complete)

        CartItem.objects.create(user=self.user1, variant=self.variant1, quantity=2)
        CartItem.objects.create(user=self.user1, variant=self.variant2, quantity=1)

        client = Client()
        client.force_login(self.user1)

        res_get = client.get('/checkout/')
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(len(res_get.context['cart_items']), 2)
        self.assertEqual(res_get.context['subtotal'], 580.0)
        self.assertTrue(res_get.context['profile_is_complete'])

        res_post = client.post('/checkout/', data={
            'first_name': self.user1.first_name,
            'last_name': self.user1.last_name,
            'email': self.user1.email,
            'phone': profile.phone,
            'address': profile.address,
            'state': profile.state,
            'district': profile.district,
            'pincode': profile.pincode,
        }, content_type='application/json')

        self.assertEqual(res_post.status_code, 200)
        data = res_post.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('amount'), 580.0)

        order = Order.objects.get(id=data.get('order_id'))
        self.assertEqual(order.total_amount, 580.0)
        self.assertEqual(order.items.count(), 2)

    def test_session_cart_merges_on_login(self):
        client = Client()
        res = client.post('/api/cart/add/', data={'variant_id': self.variant1.id, 'quantity': 3}, content_type='application/json')
        self.assertEqual(res.status_code, 200)

        from django.contrib.auth.signals import user_logged_in
        request_mock = client.request().wsgi_request
        request_mock.session = client.session
        user_logged_in.send(sender=User, request=request_mock, user=self.user1)

        cart_item = CartItem.objects.get(user=self.user1, variant=self.variant1)
        self.assertEqual(cart_item.quantity, 3)
