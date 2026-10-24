from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Product, Shop


class ProductApiTests(APITestCase):
    def test_product_crud_and_filters(self):
        shop = Shop.objects.create(name="Market", color="blue")
        category_response = self.client.post(
            "/shop/categories/",
            {"name": "Books", "description": ""},
            format="json",
        )
        self.assertEqual(category_response.status_code, status.HTTP_201_CREATED)
        category = Category.objects.get(pk=category_response.data["id"])
        other_category = Category.objects.create(name="Food")
        matching_product = Product.objects.create(
            shop=shop,
            category=category,
            title="Novel",
            price="15.00",
            stock=3,
        )
        Product.objects.create(
            shop=shop,
            category=other_category,
            title="Bread",
            price="5.00",
        )

        response = self.client.get(
            "/shop/products/",
            {
                "price__gte": "10",
                "category": category.id,
                "shop": shop.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [matching_product.id])

        create_response = self.client.post(
            "/shop/products/",
            {
                "shop": shop.id,
                "category": category.id,
                "title": "Reference",
                "price": "20.00",
                "stock": 4,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        product_id = create_response.data["id"]

        update_response = self.client.patch(
            f"/shop/products/{product_id}/",
            {"stock": 8},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["stock"], 8)

        delete_response = self.client.delete(f"/shop/products/{product_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
