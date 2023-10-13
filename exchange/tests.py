from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.db.models import Sum
import random
from .models import Seller, Transaction


class CreditExchangeAPITestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(CreditExchangeAPITestCase, cls).setUpClass()
        client = APIClient()
        token_endpoint = "/api/token/"

        seller1 = Seller.objects.create_user(username='test1', password='1234')
        seller2 = Seller.objects.create_user(username='test2', password='4321')

        cls.sellers = [seller1, seller2]

        # Getting access token for defined sellers
        token1 = client.post(token_endpoint,
                             data={'username': 'test1', 'password': '1234'},
                             format='json').data['token']
        token2 = client.post(token_endpoint,
                             data={'username': 'test2', 'password': '4321'},
                             format='json').data['token']

        cls.tokens = [f"JWT {token1}", f"JWT {token2}"]

    def setUp(self):
        self.client = APIClient()
        self.selling_endpoint = "/api/sell/"

    def tearDown(self):
        for seller in self.sellers:
            seller.credit = 0
            seller.save()
        Transaction.objects.all().delete()

    def __credit_addition(self, n=2):
        """
        Function for checking adding charge to defined seller for n times
        :param n:
        :return:
        """
        sellers_credit = [0, 0]
        for i in range(2):
            for _ in range(n):
                amount = random.randint(20, 50)
                sellers_credit[i] += amount
                Transaction.objects.create(
                    user=self.sellers[i],
                    type=Transaction.Type.CHARGE,
                    amount=amount,
                    receiver=None
                )
        return sellers_credit

    def test_credit_addition(self):
        """
        Test case for addition of charge to user credit for 5 times
        :return:
        """
        n_adds = 5
        sellers_credit = self.__credit_addition(n=n_adds)
        self.assertEquals(sellers_credit[0], self.sellers[0].credit)
        self.assertEquals(sellers_credit[1], self.sellers[1].credit)
        self.assertEquals(2 * n_adds, Transaction.objects.all().count())

    def test_selling_charge(self):
        """
        Test case for 10 times selling with random amounts,
        assuring the usage of amounts that exceed the user credit
        :return:
        """
        n_adds = 2
        sellers_credit = self.__credit_addition(n=n_adds)
        n_transactions = n_adds * 2

        for i in range(2):
            header = {
                "Authorization": self.tokens[i]
            }
            for _ in range(10):
                amount = random.randint(10, 15)
                payload = {
                    "amount": amount,
                    "receiver": "111"
                }
                response = self.client.post(self.selling_endpoint, data=payload, headers=header, format='json')

                if amount > sellers_credit[i]:
                    self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST,
                                      msg=f"amount: {amount}, credit: {sellers_credit[i]}")
                else:
                    self.assertEquals(response.status_code, status.HTTP_201_CREATED)
                    sellers_credit[i] -= amount
                    n_transactions += 1

        # Asserting calculated number of transactions with the count in database
        self.assertEquals(n_transactions, Transaction.objects.all().count())

        # Asserting user credit and the calculated user credit
        self.assertEquals(sellers_credit[0], Seller.objects.filter(username=self.sellers[0].username).first().credit)
        self.assertEquals(sellers_credit[1], Seller.objects.filter(username=self.sellers[1].username).first().credit)

        # Asserting the sum of charges and sells to equal the user credit
        for seller in self.sellers:
            charge_sum_transactions = Transaction.objects.filter(
                user=seller, type=Transaction.Type.CHARGE
            ).aggregate(total=Sum('amount'))['total']

            sell_sum_transactions = Transaction.objects.filter(
                user=seller, type=Transaction.Type.SELL
            ).aggregate(total=Sum('amount'))['total']

            self.assertEquals(charge_sum_transactions - sell_sum_transactions,
                              Seller.objects.filter(username=seller.username).first().credit)
