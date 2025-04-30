from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.rules.services import RuleService, RuleEvaluation

User = get_user_model()
evaluate_condition = RuleEvaluation.evaluate_condition
evaluate_rules = RuleEvaluation.evaluate_rules


class RuleEvaluationTests(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin1@gmail.com',
            password='password123',
            role='admin1'
        )
        self.rule_servie = RuleService()
        
    def test_simple_condition_evaluation(self):
        # Equal operator
        condition = {"field": "age", "operator": "==", "value": 18}
        self.assertTrue(evaluate_condition(condition, {"age": 18}))
        self.assertFalse(evaluate_condition(condition, {"age": 17}))
        
        # Not equal operator
        condition = {"field": "status", "operator": "!=", "value": "pending"}
        self.assertTrue(evaluate_condition(condition, {"status": "approved"}))
        self.assertFalse(evaluate_condition(condition, {"status": "pending"}))
        
        # Greater than operator
        condition = {"field": "score", "operator": ">", "value": 70}
        self.assertTrue(evaluate_condition(condition, {"score": 71}))
        self.assertFalse(evaluate_condition(condition, {"score": 70}))
        
        # Less than operator
        condition = {"field": "price", "operator": "<", "value": 100}
        self.assertTrue(evaluate_condition(condition, {"price": 99}))
        self.assertFalse(evaluate_condition(condition, {"price": 100}))
        
        # Greater than or equal operator
        condition = {"field": "age", "operator": ">=", "value": 21}
        self.assertTrue(evaluate_condition(condition, {"age": 21}))
        self.assertTrue(evaluate_condition(condition, {"age": 22}))
        self.assertFalse(evaluate_condition(condition, {"age": 20}))
        
        # Less than or equal operator
        condition = {"field": "quantity", "operator": "<=", "value": 5}
        self.assertTrue(evaluate_condition(condition, {"quantity": 5}))
        self.assertTrue(evaluate_condition(condition, {"quantity": 4}))
        self.assertFalse(evaluate_condition(condition, {"quantity": 6}))
        
        # Contains operator (list)
        condition = {"field": "tags", "operator": "contains", "value": "premium"}
        self.assertTrue(evaluate_condition(condition, {"tags": ["basic", "premium", "enterprise"]}))
        self.assertFalse(evaluate_condition(condition, {"tags": ["basic", "enterprise"]}))
        
        # Contains operator (string)
        condition = {"field": "email", "operator": "contains", "value": "gmail"}
        self.assertTrue(evaluate_condition(condition, {"email": "user@gmail.com"}))
        self.assertFalse(evaluate_condition(condition, {"email": "user@outlook.com"}))
    
    def test_nested_condition_evaluation(self):
        # AND condition
        condition = {
            "AND": [
                {"field": "age", "operator": ">=", "value": 18},
                {"field": "country", "operator": "==", "value": "Thailand"}
            ]
        }
        self.assertTrue(evaluate_condition(condition, {"age": 21, "country": "Thailand"}))
        self.assertFalse(evaluate_condition(condition, {"age": 17, "country": "Thailand"}))
        self.assertFalse(evaluate_condition(condition, {"age": 21, "country": "Japan"}))
        
        # OR condition
        condition = {
            "OR": [
                {"field": "subscription", "operator": "==", "value": "premium"},
                {"field": "referrals", "operator": ">=", "value": 5}
            ]
        }
        self.assertTrue(evaluate_condition(condition, {"subscription": "premium", "referrals": 0}))
        self.assertTrue(evaluate_condition(condition, {"subscription": "basic", "referrals": 5}))
        self.assertTrue(evaluate_condition(condition, {"subscription": "premium", "referrals": 5}))
        self.assertFalse(evaluate_condition(condition, {"subscription": "basic", "referrals": 4}))
        
        # Complex nested condition
        condition = {
            "AND": [
                {"field": "age", "operator": ">=", "value": 18},
                {
                    "OR": [
                        {"field": "country", "operator": "==", "value": "Thailand"},
                        {"field": "country", "operator": "==", "value": "Singapore"}
                    ]
                }
            ]
        }
        self.assertTrue(evaluate_condition(condition, {"age": 18, "country": "Thailand"}))
        self.assertTrue(evaluate_condition(condition, {"age": 21, "country": "Singapore"}))
        self.assertFalse(evaluate_condition(condition, {"age": 17, "country": "Thailand"}))
        self.assertFalse(evaluate_condition(condition, {"age": 21, "country": "Japan"}))
    
    def test_nested_field_access(self):
        condition = {"field": "user.profile.age", "operator": ">=", "value": 18}
        payload = {
            "user": {
                "profile": {
                    "age": 21
                }
            }
        }
        self.assertTrue(evaluate_condition(condition, payload))
        payload["user"]["profile"]["age"] = 17
        self.assertFalse(evaluate_condition(condition, payload))
        
        condition = {"field": "user.interests", "operator": "contains", "value": "music"}
        payload = {
            "user": {
                "interests": ["coding", "music", "sports"]
            }
        }
        self.assertTrue(evaluate_condition(condition, payload))
        payload["user"]["interests"] = ["coding", "sports"]
        self.assertFalse(evaluate_condition(condition, payload))
    
    def test_missing_nested_fields(self):
        condition = {"field": "user.profile.age", "operator": ">=", "value": 18}
        
        payload = {"user": {"name": "John"}}
        self.assertFalse(evaluate_condition(condition, payload))
        
        payload = {"user": {}}
        self.assertFalse(evaluate_condition(condition, payload))
        
        payload = {}
        self.assertFalse(evaluate_condition(condition, payload))
        
    def test_complex_nested_condtion_and_field(self):
        condition = {
            "AND": [
                {"field": "user.age", "operator": ">=", "value": 18},
                {
                    "OR": [
                        {"field": "user.subscription", "operator": "==", "value": "premium"},
                        {
                            "AND": [
                                {"field": "user.subscription", "operator": "==", "value": "basic"},
                                {"field": "user.account_age_days", "operator": ">=", "value": 90}
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Premium subscription
        payload = {
            "user": {
                "age": 25,
                "subscription": "premium",
                "account_age_days": 30
            }
        }
        self.assertTrue(evaluate_condition(condition, payload))
        
        # Basic subscription but old account
        payload = {
            "user": {
                "age": 25,
                "subscription": "basic",
                "account_age_days": 95
            }
        }
        self.assertTrue(evaluate_condition(condition, payload))
        
        # Basic subscription but new account
        payload = {
            "user": {
                "age": 25,
                "subscription": "basic",
                "account_age_days": 30
            }
        }
        self.assertFalse(evaluate_condition(condition, payload))
        
        # Underage user
        payload = {
            "user": {
                "age": 17,
                "subscription": "premium",
                "account_age_days": 30
            }
        }
        self.assertFalse(evaluate_condition(condition, payload))
        
    def test_multiple_rules_evaluation(self):
        rule_conditions = [
            ("Age Check", {"field": "age", "operator": ">=", "value": 18}),
            ("Country Check", {"field": "country", "operator": "==", "value": "Thailand"})
        ]
        
        # All rules pass
        result = evaluate_rules(rule_conditions, {"age": 21, "country": "Thailand"})
        self.assertEqual(result["passed_rules"], ["Age Check", "Country Check"])
        self.assertEqual(result["failed_rules"], [])
        
        # Some rules fail
        result = evaluate_rules(rule_conditions, {"age": 17, "country": "Thailand"})
        self.assertEqual(result["passed_rules"], ["Country Check"])
        self.assertEqual(result["failed_rules"], ["Age Check"])
        
        # All rules fail
        result = evaluate_rules(rule_conditions, {"age": 17, "country": "Japan"})
        self.assertEqual(result["passed_rules"], [])
        self.assertEqual(result["failed_rules"], ["Age Check", "Country Check"])

    def test_rule_database_storage(self):
        condition = {
            "AND": [
                {"field": "user.profile.subscription_type", "operator": "==", "value": "premium"},
                {"field": "user.profile.account_age_days", "operator": ">=", "value": 30},
                {"field": "user.contact.email_verified", "operator": "==", "value": True}
            ]
        }
        
        rule = self.rule_servie.create(
            name="Premium User Verification",
            condition=condition,
            created_by=self.admin_user
        )
        
        retrieved_rule = self.rule_servie.find(id=rule.id)
        
        # Check that the condition was stored correctly
        self.assertEqual(retrieved_rule.condition, condition)
        
        # Test retrieving by names
        rule_conditions = self.rule_servie.get_rules_by_names(["Premium User Verification"])
        self.assertEqual(len(rule_conditions), 1)
        self.assertEqual(rule_conditions[0][0], "Premium User Verification")
        self.assertEqual(rule_conditions[0][1], condition)


class ComplexRuleAPITests(TestCase):
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin1@gmail.com',
            password='password123',
            role='admin'
        )
        self.client_user = User.objects.create_user(
            email='client1@gmail.com',
            password='password123',
            role='client'
        )
        self.rule_servie = RuleService()
        self.api_client = APIClient()
        self.rule_url = '/api/rules/'
        self.evaluate_url = '/api/rule-evaluation/evaluate/'
    
    def test_create_complex_rule(self):
        # Create the rules as admin
        self.api_client.force_authenticate(user=self.admin_user)
        
        data = {
            "name": "Premium User Verification",
            "condition": {
                "AND": [
                    {
                        "field": "user.profile.subscription_type",
                        "operator": "==",
                        "value": "premium"
                    },
                    {
                        "field": "user.profile.account_age_days",
                        "operator": ">=",
                        "value": 30
                    },
                    {
                        "OR": [
                            {
                                "field": "user.contact.email_verified",
                                "operator": "==",
                                "value": True
                            },
                            {
                                "field": "user.contact.phone_verified",
                                "operator": "==",
                                "value": True
                            }
                        ]
                    }
                ]
            },
            "is_active": True
        }
        response = self.api_client.post(self.rule_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the rule was created correctly
        rule = self.rule_servie.find(name='Premium User Verification')
        self.assertEqual(rule.condition, data['condition'])
        
        # Check if cannot create rule as client
        self.api_client.force_authenticate(user=self.client_user)
        response = self.api_client.post(self.rule_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_evaluate_complex_rule(self):
        # Create the rules as admin
        self.api_client.force_authenticate(user=self.admin_user)
        rule_data = {
            "name": "Complex Eligibility",
            "condition": {
                "AND": [
                    {
                        "field": "applicant.age",
                        "operator": ">=",
                        "value": 18
                    },
                    {
                        "OR": [
                            {
                                "AND": [
                                    {
                                        "field": "applicant.employment.status",
                                        "operator": "==",
                                        "value": "employed"
                                    },
                                    {
                                        "field": "applicant.employment.years",
                                        "operator": ">=",
                                        "value": 2
                                    }
                                ]
                            },
                            {
                                "AND": [
                                    {
                                        "field": "applicant.student",
                                        "operator": "==",
                                        "value": True
                                    },
                                    {
                                        "field": "applicant.gpa",
                                        "operator": ">=",
                                        "value": 3.0
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            "is_active": True
        }
        response = self.api_client.post(self.rule_url, rule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Evaluatie the payloads as client
        self.api_client.force_authenticate(user=self.client_user)
        
        # Adult with sufficient work experience
        evaluation_data = {
            "rules": ["Complex Eligibility"],
            "payload": {
                "applicant": {
                    "age": 30,
                    "employment": {
                        "status": "employed",
                        "years": 5,
                        "position": "Developer"
                    },
                    "student": False
                }
            }
        }
        response = self.api_client.post(self.evaluate_url, evaluation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('result'), 'APPROVED')
        
        # Student with good GPA
        evaluation_data = {
            "rules": ["Complex Eligibility"],
            "payload": {
                "applicant": {
                    "age": 20,
                    "student": True,
                    "gpa": 3.8,
                    "university": "Example University"
                }
            }
        }
        response = self.api_client.post(self.evaluate_url, evaluation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('result'), 'APPROVED')
        
        # Underage applicant
        evaluation_data = {
            "rules": ["Complex Eligibility"],
            "payload": {
                "applicant": {
                    "age": 17,
                    "employment": {
                        "status": "employed",
                        "years": 3
                    }
                }
            }
        }
        response = self.api_client.post(self.evaluate_url, evaluation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('result'), 'REJECTED')
        
        # Adult with insufficient employment
        evaluation_data = {
            "rules": ["Complex Eligibility"],
            "payload": {
                "applicant": {
                    "age": 25,
                    "employment": {
                        "status": "employed",
                        "years": 1
                    },
                    "student": False
                }
            }
        }
        response = self.api_client.post(self.evaluate_url, evaluation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('result'), 'REJECTED')
    
    def test_evaluate_multiple_complex_rules(self):
        # Create the rules as admin
        self.api_client.force_authenticate(user=self.admin_user)
        
        rule1_data = {
            "name": "Age and Location Check",
            "condition": {
                "AND": [
                    {"field": "person.age", "operator": ">=", "value": 21},
                    {
                        "OR": [
                            {"field": "person.location.country", "operator": "==", "value": "USA"},
                            {"field": "person.location.country", "operator": "==", "value": "Canada"}
                        ]
                    }
                ]
            },
            "is_active": True
        }
        response1 = self.api_client.post(self.rule_url, rule1_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        rule2_data = {
            "name": "Credit Score Check",
            "condition": {
                "AND": [
                    {"field": "person.credit.score", "operator": ">=", "value": 700},
                    {"field": "person.credit.history_years", "operator": ">=", "value": 2}
                ]
            },
            "is_active": True
        }
        response2 = self.api_client.post(self.rule_url, rule2_data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Evaluatie the payloads as client
        self.api_client.force_authenticate(user=self.client_user)
        
        # Payload that passes both rules
        evaluation_data = {
            "rules": ["Age and Location Check", "Credit Score Check"],
            "payload": {
                "person": {
                    "age": 25,
                    "location": {
                        "country": "USA",
                        "state": "California"
                    },
                    "credit": {
                        "score": 750,
                        "history_years": 5
                    }
                }
            }
        }
        response = self.api_client.post(self.evaluate_url, evaluation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_data = response.data
        self.assertEqual(result_data.get('result'), 'APPROVED')
        self.assertEqual(set(result_data.get('passed_rules')), {'Age and Location Check', 'Credit Score Check'})
        self.assertEqual(result_data.get('failed_rules'), [])
        
        # Payload that fails one rule
        evaluation_data = {
            "rules": ["Age and Location Check", "Credit Score Check"],
            "payload": {
                "person": {
                    "age": 25,
                    "location": {
                        "country": "USA",
                        "state": "California"
                    },
                    "credit": {
                        "score": 650,
                        "history_years": 5
                    }
                }
            }
        }
        response = self.api_client.post(self.evaluate_url, evaluation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_data = response.data
        self.assertEqual(result_data.get('result'), 'REJECTED')
        self.assertEqual(result_data.get('passed_rules'), ['Age and Location Check'])
        self.assertEqual(result_data.get('failed_rules'), ['Credit Score Check'])
    
    def test_rule_with_deeply_nested_structure(self):
        # Create the rules as admin
        self.api_client.force_authenticate(user=self.admin_user)
        
        rule_data = {
            "name": "Deep Structure Check",
            "condition": {
                "AND": [
                    {"field": "data.user.profile.settings.privacy.allow_messaging", "operator": "==", "value": True},
                    {"field": "data.user.profile.settings.notifications.email.marketing", "operator": "==", "value": True},
                    {"field": "data.meta.client.version", "operator": ">=", "value": "2.0.0"}
                ]
            },
            "is_active": True
        }
        response = self.api_client.post(self.rule_url, rule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Evaluatie the payloads as client
        self.api_client.force_authenticate(user=self.client_user)
        
        evaluation_data = {
            "rules": ["Deep Structure Check"],
            "payload": {
                "data": {
                    "user": {
                        "id": 123,
                        "profile": {
                            "name": "Test User",
                            "settings": {
                                "privacy": {
                                    "allow_messaging": True,
                                    "show_online_status": False
                                },
                                "notifications": {
                                    "email": {
                                        "marketing": True,
                                        "updates": False
                                    },
                                    "push": {
                                        "enabled": True
                                    }
                                }
                            }
                        }
                    },
                    "meta": {
                        "client": {
                            "name": "Mobile App",
                            "version": "2.5.0",
                            "platform": "iOS"
                        }
                    }
                }
            }
        }
        response = self.api_client.post(self.evaluate_url, evaluation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('result'), 'APPROVED')
        
        # Change one value to make it fail
        evaluation_data["payload"]["data"]["user"]["profile"]["settings"]["notifications"]["email"]["marketing"] = False
        response = self.api_client.post(self.evaluate_url, evaluation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('result'), 'REJECTED')

    def test_rule_name_uniqueness(self):
        # Create the rules as admin
        self.api_client.force_authenticate(user=self.admin_user)

        self.rule_servie.create(
            name="Unique Test Rule",
            condition={"field": "status", "operator": "==", "value": "active"},
            created_by=self.admin_user
        )
        
        rule_data = {
            "name": "Unique Test Rule",
            "condition": {
                "field": "age",
                "operator": ">=",
                "value": 18
            },
            "is_active": True
        }
        response = self.api_client.post(self.rule_url, rule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_evaluate_inactive_rule(self):
        # Create the rules as admin
        self.api_client.force_authenticate(user=self.admin_user)
        self.rule_servie.create(
            name="Inactive Rule",
            condition={"field": "status", "operator": "==", "value": "active"},
            created_by=self.admin_user,
            is_active=False
        )
        
        # Evaluatie the payloads as client
        self.api_client.force_authenticate(user=self.client_user)
        evaluation_data = {
            'rules': ['Inactive Rule'],
            'payload': {
                'status': 'active'
            }
        }
        response = self.api_client.post(self.evaluate_url, evaluation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Rule was not found.', response.data.get('detail', ''))

    def test_api_create_invalid_rule(self):
        # Create the rules as admin
        self.api_client.force_authenticate(user=self.admin_user)
        rule_data = {
            "name": "Invalid Rule",
            "condition": {
                "field": "age",
                "operator": "invalid_op",
                "value": 18
            },
            "is_active": True
        }
        response = self.api_client.post(self.rule_url, rule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Creating the rule with missing required field 'operator'
        rule_data = {
            "name": "Invalid Rule",
            "condition": {
                "field": "age",
                "value": 18
            },
            "is_active": True
        }
        response = self.api_client.post(self.rule_url, rule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_api_evaluate_nonexistent_rule(self):
        # Evaluatie the payloads as client
        self.api_client.force_authenticate(user=self.client_user)
        evaluation_data = {
            "rules": ["Non-existent Rule"],
            "payload": {
                "age": 25
            }
        }
        response = self.api_client.post(self.evaluate_url, evaluation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Rule was not found.', response.data.get('detail', ''))
