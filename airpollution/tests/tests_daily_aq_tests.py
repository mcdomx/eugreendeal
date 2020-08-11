"""
Author: Carly Gloge
Test for the map of daily pollution data
"""
from django.test import TestCase
from airpollution.views import daily_aq_map
from django.http import HttpRequest

class TestDailyAQMap(TestCase):
    def setUp(self):
        self.start_date = "2020-04-01"
        self.end_date = "2020-04-30"
        
    def test_daily_aq_map(self):
        
        request = HttpRequest()
        
        request.method = 'GET'
        request.path = "/daily_aq/?start_date=" + self.start_date + "&end_date=" + self.end_date
        
        response = daily_aq_map.draw_map(request)
        
        self.assertEqual(response.status_code, 200)
        
    
    
    
    
