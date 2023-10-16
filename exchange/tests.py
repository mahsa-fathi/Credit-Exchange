from django.test import TransactionTestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.db.models import Sum
import time
import random
import threading
from .models import Seller, Transaction


RESPONSE_TIME = 0


class CreditExchangeTestCase(TransactionTestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.selling_endpoint = "/api/sell/"
        token_endpoint = "/api/token/"

        seller1 = Seller.objects.create_user(username='test1', password='1234')
        seller2 = Seller.objects.create_user(username='test2', password='4321')

        self.sellers = [seller1, seller2]

        # Getting access token for defined sellers
        token1 = self.client.post(token_endpoint,
                                  data={'username': 'test1', 'password': '1234'},
                                  format='json').data['token']
        token2 = self.client.post(token_endpoint,
                                  data={'username': 'test2', 'password': '4321'},
                                  format='json').data['token']

        self.tokens = [f"JWT {token1}", f"JWT {token2}"]

    def tearDown(self) -> None:
        global RESPONSE_TIME
        RESPONSE_TIME = 0
        Seller.objects.all().delete()
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

    def __send_sell_request(self, token):
        header = {
            "Authorization": token
        }

        amount = random.randint(1, 15)
        payload = {
            "amount": amount,
            "receiver": "111"
        }
        response = self.client.post(self.selling_endpoint, data=payload, headers=header, format='json')

        return amount, response.status_code

    def __send_sell_request_timer(self, token):
        header = {
            "Authorization": token
        }

        amount = random.randint(1, 15)
        payload = {
            "amount": amount,
            "receiver": "111"
        }
        start_time = time.time()
        self.client.post(self.selling_endpoint, data=payload, headers=header, format='json')
        end_time = time.time()

        response_time = (end_time - start_time) * 1000
        global RESPONSE_TIME
        RESPONSE_TIME += response_time

        return response_time

    def assertTransactionsAndCredit(self, seller):
        seller.refresh_from_db()
        charge_sum_transactions = Transaction.objects.filter(
            user=seller, type=Transaction.Type.CHARGE
        ).aggregate(total=Sum('amount'))['total']

        sell_sum_transactions = Transaction.objects.filter(
            user=seller, type=Transaction.Type.SELL
        ).aggregate(total=Sum('amount'))['total']

        tot_transactions = charge_sum_transactions - sell_sum_transactions

        self.assertEquals(tot_transactions, seller.credit,
                          msg=f"Transactions: {tot_transactions} and credit: {seller.credit} are not the same")
        self.assertGreaterEqual(seller.credit, 0, msg=f"Credit {seller.credit} should be more than 0.")

    def __test_selling_charge(self, n_adds, n_reqs):
        """
        Test case common code for n_reqs times selling with random amounts,
        assuring the usage of amounts that exceed the user credit
        :return:
        """
        sellers_credit = self.__credit_addition(n=n_adds)

        for i in range(2):
            for _ in range(n_reqs):
                amount, status_code = self.__send_sell_request(self.tokens[i])

                if amount > sellers_credit[i]:
                    self.assertEquals(status_code, status.HTTP_400_BAD_REQUEST,
                                      msg=f"amount: {amount}, credit: {sellers_credit[i]}")
                else:
                    self.assertEquals(status_code, status.HTTP_201_CREATED)
                    sellers_credit[i] -= amount

        # Asserting the sum of charges and sells to equal the user credit
        for seller in self.sellers:
            self.assertTransactionsAndCredit(seller)

    def test_credit_addition(self):
        """
        Test case for addition of charge to user credit for 5 times
        :return:
        """
        n_adds = 5
        sellers_credit = self.__credit_addition(n=n_adds)
        self.sellers[0].refresh_from_db()
        self.sellers[1].refresh_from_db()
        self.assertEquals(sellers_credit[0], self.sellers[0].credit,
                          msg=f"seller's credit should be {sellers_credit[0]} but is {self.sellers[0].credit}")
        self.assertEquals(sellers_credit[1], self.sellers[1].credit,
                          msg=f"seller's credit should be {sellers_credit[1]} but is {self.sellers[1].credit}")
        self.assertEquals(2 * n_adds, Transaction.objects.all().count())

    def test_selling_charge_ten_requests(self):
        """
        Test case for 10 times selling with random amounts,
        assuring the usage of amounts that exceed the user credit
        :return:
        """
        self.__test_selling_charge(n_adds=2, n_reqs=10)

    def test_selling_charge_thousand_requests(self):
        """
        Test case for 1000 times selling with random amounts,
        assuring the usage of amounts that exceed the user credit
        :return:
        """
        self.__test_selling_charge(n_adds=100, n_reqs=1000)

    def test_sim_selling_charge(self):
        n_adds = 10
        self.__credit_addition(n=n_adds)

        num_threads = 10
        threads = []
        for i in range(2):
            for _ in range(num_threads):
                thread = threading.Thread(target=self.__send_sell_request, args=(self.tokens[i],))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

        # Asserting the sum of charges and sells to equal the user credit
        for seller in self.sellers:
            self.assertTransactionsAndCredit(seller)

    def test_sim_selling_charge_response_time(self):
        n_adds = 10
        self.__credit_addition(n=n_adds)

        num_threads = 20
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=self.__send_sell_request_timer, args=(self.tokens[0],))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        global RESPONSE_TIME
        print(f"Average Response Time for 20 requests: {RESPONSE_TIME / 20} ms")

        # Asserting the sum of charges and sells to equal the user credit
        self.assertTransactionsAndCredit(seller=self.sellers[0])

    def test_selling_charge_response_time(self):
        n_adds = 1
        self.__credit_addition(n=n_adds)

        self.__send_sell_request_timer(self.tokens[0])

        global RESPONSE_TIME
        print(f"Average Response Time for 1 request: {RESPONSE_TIME} ms")

        # Asserting the sum of charges and sells to equal the user credit
        self.assertTransactionsAndCredit(seller=self.sellers[0])
