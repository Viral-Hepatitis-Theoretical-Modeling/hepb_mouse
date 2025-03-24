# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 18:40:15 2020

@author: eric
"""

import os
import unittest
import random as py_rand
from hepcep_model import *
from repast4py import parameters


class TestZones(unittest.TestCase):

    def setUp(self):
        py_rand.seed(1)       # Set python random seed

        self.params = init_params('./data/model_props.yaml', '')

        self.data_dir = 'data'

    def test_zone(self):
        zone_data = {'Zipcode':60606, 'Drug_Market':1, 'lat':88.12, 'lon':41.23}
        distances = {DrugName.BUPRENORPHINE: 0.5, DrugName.METHADONE: 0.5, DrugName.NALTREXONE: 0.5}
        zone = Zone(zone_data, distances)

        self.assertIsNotNone(zone)
        self.assertEqual(zone.zip_code, 60606)
        self.assertEqual(zone.drug_market, 1)
        self.assertEqual(zone.lat, 88.12)
        self.assertEqual(zone.lon, 41.23)

    def test_load_opioid_treatment_distances(self):
        distances = load_opioid_treatment_distances(self.data_dir, 'REAL')
        self.assertEqual(distances[60626][DrugName.BUPRENORPHINE], 0.0442)

        distances = load_opioid_treatment_distances(self.data_dir, 'SCENARIO_3')
        self.assertEqual(distances[60606][DrugName.NALTREXONE], 1.5785)

    def test_load_zones(self):
        zones = load_zones(self.data_dir)

        self.assertIsNotNone(zones)

        zone = zones[60005]

        # Should match data in the zones file
        #60005,0,42.02424808665833,-87.9527896873431
        self.assertIsNotNone(zone)
        self.assertEqual(zone.zip_code, 60005)
        self.assertEqual(zone.drug_market, 0)
        self.assertAlmostEqual(zone.lat, 42.0242, 3)
        self.assertAlmostEqual(zone.lon,-87.9527, 3)

        self.assertEqual(len(zones), 298)
        
    def test_load_zone_distances(self):
        zones_dists = load_zone_distances(self.data_dir)

        self.assertIsNotNone(zones_dists)

        zipcode = 60605
        dists_1 = zones_dists[zipcode]
        self.assertIsNotNone(dists_1)
        
        # Check the distance from the zipcode to itself (should be zero)
        d = dists_1[zipcode]
        self.assertEqual(d, 0)

        # Check distance to another zipcode
        d = dists_1[60002]
        self.assertAlmostEqual(d, 76.7124, 3)

class testPersons(unittest.TestCase):
    def setUp(self):
        py_rand.seed(1)       # Set python random seed

        self.params = init_params('./data/model_props.yaml', '')
        self.params[OUTPUT_DIRECTORY] = './tests/output/'

        self.data_dir = 'data'

        from mpi4py import MPI
        self.runner = schedule.init_schedule_runner(MPI.COMM_WORLD)

        output_dir = parameters.params[OUTPUT_DIRECTORY]
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        Distributions() # Initialize Distributions
        Statistics(zone_map={})  # Initialize Statistics singleton

    def tearDown(self) -> None:
        Statistics.getInstance().close()

    def test_person(self):
        person_data = {
            'ID':1,
            'Age':16.98,
            'Age_Started':15,
            'Gender':'Male',
            'Race':'NHWhite',
            'Syringe_source':'HR',
            'Zip':60520,
            'HCV':'susceptible',
            'Drug_in_degree':0,
            'Drug_out_degree':0,
            'Daily_injection_intensity':0.1333,
            'Fraction_recept_sharing':0
            }

        person = Person(1, person_data, 0)
        self.assertIsNotNone(person)
        self.assertEqual(person.age, 16.98)
        self.assertEqual(person.zipcode, 60520)

    def test_load_CNEP(self):
        # person data is a pandas.DataFrame
        person_data = load_cnep_data(self.data_dir)

        self.assertIsNotNone(person_data)
        self.assertAlmostEqual(person_data.iloc[1]['Age'], 17.01, 2)
        self.assertEqual(person_data.iloc[1]['Gender'], 'Male')

    def test_create_persons(self):
        # person data is a pandas.DataFrame
        person_data = load_cnep_data(self.data_dir)
        zones = load_zones(self.data_dir)
        self.assertIsNotNone(person_data)

        rank = 0
        person_creator = PersonCreator( person_data, rank)
        self.assertIsNotNone(person_creator)

        tick = 0
        person_count = 1000
        early_career_only = False
        persons = person_creator.create_persons(tick, person_count, None, zones, early_career_only)

        self.assertIsNotNone(persons)
        self.assertEqual(len(persons),person_count)

        person_count = 500
        early_career_only = True
        persons = person_creator.create_persons(tick, person_count, None, zones, early_career_only)
        self.assertIsNotNone(persons)
        self.assertEqual(len(persons),person_count)

        # Check that the young early career flag works
        found_old = 0
        thresh = self.params[MATURITY_THRESHOLD]
        for p in persons:
            if (p.age - p.age_started) > thresh:
                found_old += 1

        self.assertEqual(found_old, 0)

class TestLoadViralLoads(unittest.TestCase):

    def setUp(self):
        py_rand.seed(1)       # Set python random seed

        self.params = init_params('./data/model_props.yaml', '')

        self.data_dir = 'data'

    def test_load_time_series(self):
        vk_file = self.params[VK_ACUTE_INFECT_CLEAR_FILE]
        
        viral_loads = load_viral_load_series(os.path.join(self.data_dir,vk_file))
        self.assertIsNotNone(viral_loads)

        series_ID = 1
        load_values = viral_loads[series_ID]
        self.assertIsNotNone(load_values)
        self.assertEqual(load_values[2],-0.634)  # dependes on value in VK file

    def test_load_transmit_probs(self):
        transmit_file = self.params[VK_TRANSMIT_PROB_FILE]
        transmit_probs = load_transmission_probabilities(os.path.join(self.data_dir,transmit_file))

        self.assertIsNotNone(transmit_probs)
        

class TestViralKineticsData(unittest.TestCase):

    def setUp(self):
        py_rand.seed(1)       # Set python random seed

        self.params = init_params('./data/model_props.yaml', '')

        self.data_dir = 'data'

        ViralKinetics(self.data_dir)

    def test_load_time_series(self):
        viral_load = ViralKinetics.getInstance().get_viral_load(VKProfile.ACUTE_INFECTION_CLEARANCE, 2, 5)

        self.assertIsNotNone(viral_load)

        # dependes on value in VK file
        self.assertEqual(viral_load, 2.49) 

    def test_transmit_prob(self):

        viral_load = 0.25
        transmit_prob = ViralKinetics.getInstance().get_transmission_probability(viral_load)

        self.assertEqual(transmit_prob,0.000383293)

        viral_load = 3.52
        transmit_prob = ViralKinetics.getInstance().get_transmission_probability(viral_load)

        self.assertEqual(transmit_prob,0.503931679)

        viral_load = 6.95
        transmit_prob = ViralKinetics.getInstance().get_transmission_probability(viral_load)

        self.assertEqual(transmit_prob,1.0)

    

if __name__ == '__main__':
    unittest.main()