#!/usr/bin/python

import unittest
import omniture
import os

creds = {}
creds['username'] = os.environ['OMNITURE_USERNAME']
creds['secret'] = os.environ['OMNITURE_SECRET']

class ElementTest(unittest.TestCase):
    def setUp(self):
        fake_list = [{"id":"123","title":"ABC"},{"id":"456","title":"DEF"}]
        self.valueList = omniture.elements.Value.list("metrics",fake_list,"test")

    def test__repr__(self):
        self.assertEqual(self.valueList.__repr__(),"<AddressableList>",\
                         "The value for __repr__ on the AddressableList was {}"\
                         .format(self.valueList.__repr__()))

    def test_value__repr__(self):
        self.assertEqual(self.valueList[0].__repr__(),"<ABC: 123 in test>", \
                         "The value of the first item in the AddressableList \
                         was {}".format(self.valueList[0].__repr__()))

    def test_value__copy__(self):
        value = self.valueList[0].copy()
        self.assertEqual(value.__repr__(), self.valueList[0].__repr__(),\
                         "The copied value was: {} the original was: {}"\
                         .format(value, self.valueList[0]))

    def test_repr_html_(self):
        self.assertEqual(self.valueList[0]._repr_html_(),\
                         "<td><b>123</b></td><td>ABC</td>",\
                         "The html value was: {}"\
                         .format(self.valueList[0]._repr_html_()))

    def test__str__(self):
        self.assertEqual(self.valueList[0].__str__(),\
                          "ID 123                       | Name: ABC \n",\
                          "__str__ returned: {}"\
                          .format(self.valueList[0].__str__()))

if __name__ == '__main__':
    unittest.main()
