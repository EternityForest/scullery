

import unittest
from scullery import mnemonics
from scullery import units

class TestMisc(unittest.TestCase):
    def test_wordlist(self):
        self.assertEqual(len(mnemonics.wordlist),1633)
            
    def test_hash(self):
        "This just happens to be what you get if you hash that string"
        self.assertEqual(mnemonics.memorableBlakeHash(b'',3,''), 'initialpuzzlegroup')

            
    def test_hash8(self):
        "Test with a longer requested result"
        self.assertEqual(mnemonics.memorableBlakeHash(b'',8,''), 'initialpuzzlegroupdeclarefactoragendalorenzoacademy')
  

    def test_conversions(self):
        "Test with a longer requested result"
        self.assertEqual(units.convert(12,"in","ft"), 1)
        self.assertEqual(units.convert(1,"km","m"), 1000)
        self.assertAlmostEqual(units.convert(50,"degC","degF"), 122)
        self.assertAlmostEqual(units.convert(122,"degF","degC"), 50)
        self.assertAlmostEqual(units.convert(1,"kft","in"), 12000)
        #Milli-inches?
        self.assertAlmostEqual(units.convert(1,"ft","min"), 12000)


    def test_nonsense_convert(self):
        with self.assertRaises(Exception):
            units.convert("80","trashpiles","garbages")
        #Can't use SI prefixes with nonlinear units like degrees
        with self.assertRaises(Exception):
            units.convert("80","mdegC","K")


  