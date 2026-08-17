#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kredi kartı asgari ödeme + devreden borç testleri."""

import json
import os
import tempfile
import unittest

import finans_server as fs


def kk_create(client, tutar=100000, asgari=40000, vade='2026-08-15', aciklama='Test KK'):
    r = client.post('/api/odemeler', json={
        'entity': 'solariz', 'aciklama': aciklama, 'tip': 'kredi-karti',
        'tutar': tutar, 'asgari_tutar': asgari, 'para': 'TL', 'vade': vade,
        'durum': 'bekliyor', 'tekrar': 'tek', 'not': 'test', 'banka': 'Garanti',
        'kaydeden': 'test'
    })
    assert r.status_code == 200
    return json.loads(r.data)['id']


def kk_pay(client, oid, tutar, tarih='2026-08-10'):
    r = client.post(f'/api/odemeler/{oid}/odendi', json={
        'odenen_tutar': tutar, 'odeme_tarihi': tarih, 'kaydeden': 'test'
    })
    return r.status_code, json.loads(r.data)


def get_odeme(client, oid):
    rows = json.loads(client.get('/api/odemeler').data)
    return next(x for x in rows if x['id'] == oid)


def aktif_kalan_toplam(rows):
    total = 0.0
    for o in rows:
        if o.get('durum') in ('odendi', 'asgari_odendi'):
            continue
        tutar = float(o.get('tutar') or 0)
        odenen = float(o.get('odenen_tutar') or 0)
        total += max(0.0, tutar - odenen)
    return round(total, 2)


class KrediKartiAsgariDevirTest(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.db_fd)
        fs.DB_PATH = self.db_path
        fs.init_db()
        self.client = fs.app.test_client()

    def tearDown(self):
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def test_t1_tam_odeme_odendi_devir_yok(self):
        oid = kk_create(self.client)
        code, data = kk_pay(self.client, oid, 100000)
        self.assertEqual(code, 200)
        self.assertEqual(data['durum'], 'odendi')
        self.assertNotIn('devreden_id', data)
        o = get_odeme(self.client, oid)
        self.assertEqual(o['durum'], 'odendi')
        devir = [x for x in json.loads(self.client.get('/api/odemeler').data) if x.get('devreden_from_id') == oid]
        self.assertEqual(len(devir), 0)

    def test_t2_asgari_odeme_devir_60k(self):
        oid = kk_create(self.client)
        code, data = kk_pay(self.client, oid, 40000)
        self.assertEqual(code, 200)
        self.assertEqual(data['durum'], 'asgari_odendi')
        self.assertIn('devreden_id', data)
        o = get_odeme(self.client, oid)
        self.assertEqual(o['durum'], 'asgari_odendi')
        self.assertAlmostEqual(float(o['odenen_tutar']), 40000, places=2)
        devir = get_odeme(self.client, data['devreden_id'])
        self.assertEqual(float(devir['tutar']), 60000)
        self.assertEqual(devir['devreden_from_id'], oid)
        self.assertEqual(devir['vade'], '2026-09-15')

    def test_t3_asgari_alti_bekliyor_devir_yok(self):
        oid = kk_create(self.client)
        code, data = kk_pay(self.client, oid, 20000)
        self.assertEqual(code, 200)
        self.assertEqual(data['durum'], 'bekliyor')
        o = get_odeme(self.client, oid)
        self.assertEqual(o['durum'], 'bekliyor')
        self.assertAlmostEqual(float(o['odenen_tutar']), 20000, places=2)
        devir = [x for x in json.loads(self.client.get('/api/odemeler').data) if x.get('devreden_from_id')]
        self.assertEqual(len(devir), 0)

    def test_t4_devir_artı_yeni_donem_90k(self):
        oid = kk_create(self.client, aciklama='KK-A')
        kk_pay(self.client, oid, 40000)
        kk_create(self.client, tutar=30000, asgari=0, vade='2026-09-20', aciklama='KK-A yeni')
        rows = json.loads(self.client.get('/api/odemeler').data)
        self.assertAlmostEqual(aktif_kalan_toplam(rows), 90000, places=2)

    def test_t5_endpoint_retry_tek_devir(self):
        oid = kk_create(self.client)
        code1, _ = kk_pay(self.client, oid, 40000)
        self.assertEqual(code1, 200)
        conn = fs.get_db()
        fs.sync_odeme_odenen(conn, oid)
        fs.sync_odeme_odenen(conn, oid)
        conn.commit()
        conn.close()
        devir = [x for x in json.loads(self.client.get('/api/odemeler').data) if x.get('devreden_from_id') == oid]
        self.assertEqual(len(devir), 1)
        code2, _ = kk_pay(self.client, oid, 1000)
        self.assertEqual(code2, 400)

    def test_t6_10k_sonra_30k_asgari_devir(self):
        oid = kk_create(self.client)
        kk_pay(self.client, oid, 10000)
        o1 = get_odeme(self.client, oid)
        self.assertEqual(o1['durum'], 'bekliyor')
        code, data = kk_pay(self.client, oid, 30000)
        self.assertEqual(code, 200)
        self.assertEqual(data['durum'], 'asgari_odendi')
        self.assertAlmostEqual(float(get_odeme(self.client, oid)['odenen_tutar']), 40000, places=2)

    def test_t7_devir_tam_odeme(self):
        oid = kk_create(self.client)
        _, data = kk_pay(self.client, oid, 40000)
        did = data['devreden_id']
        code, pdata = kk_pay(self.client, did, 60000)
        self.assertEqual(code, 200)
        self.assertEqual(pdata['durum'], 'odendi')
        self.assertAlmostEqual(pdata['kalan'], 0, places=2)

    def test_t8_tedarikci_regression(self):
        r = self.client.post('/api/odemeler', json={
            'entity': 'solariz', 'aciklama': 'Cari X', 'tip': 'tedarikci',
            'tutar': 5000, 'para': 'TL', 'vade': '2026-08-20', 'durum': 'bekliyor',
            'kaydeden': 'test'
        })
        oid = json.loads(r.data)['id']
        code, data = kk_pay(self.client, oid, 2000)
        self.assertEqual(code, 200)
        self.assertEqual(data['durum'], 'bekliyor')
        o = get_odeme(self.client, oid)
        self.assertEqual(o['durum'], 'bekliyor')

    def test_t9_taksit_regression_kredi_baglantisi(self):
        kr = self.client.post('/api/krediler', json={
            'entity': 'solariz', 'ad': 'Test', 'tip': 'bireysel', 'toplam': 1000,
            'taksit': 100, 'kalan_taksit': 10, 'kaydeden': 'test'
        })
        kid = json.loads(kr.data)['id']
        orr = self.client.post('/api/odemeler', json={
            'entity': 'solariz', 'aciklama': 'Taksit 1', 'tip': 'taksit',
            'tutar': 100, 'vade': '2026-08-20', 'kredi_id': kid, 'kaydeden': 'test'
        })
        oid = json.loads(orr.data)['id']
        code, data = kk_pay(self.client, oid, 100)
        self.assertEqual(code, 200)
        self.assertEqual(data['durum'], 'odendi')

    def test_t10_invalid_id_404(self):
        r = self.client.post('/api/odemeler/invalid-id-xyz/odendi', json={'odenen_tutar': 100})
        self.assertEqual(r.status_code, 404)

    def test_t11_manuel_odendi_reddedilir(self):
        oid = kk_create(self.client)
        kk_pay(self.client, oid, 20000)
        r = self.client.put(f'/api/odemeler/{oid}', json={
            'entity': 'solariz', 'aciklama': 'Test KK', 'tip': 'kredi-karti',
            'tutar': 100000, 'para': 'TL', 'vade': '2026-08-15', 'odeme_tarihi': '',
            'durum': 'odendi', 'tekrar': 'tek', 'not': 'x', 'asgari_tutar': 40000,
            'guncelleyen': 'test'
        })
        self.assertEqual(r.status_code, 400)
        o = get_odeme(self.client, oid)
        self.assertNotEqual(o['durum'], 'odendi')

    def test_t12_asgari_odendi_tek_kez_sayilir(self):
        oid = kk_create(self.client)
        kk_pay(self.client, oid, 40000)
        rows = json.loads(self.client.get('/api/odemeler').data)
        self.assertAlmostEqual(aktif_kalan_toplam(rows), 60000, places=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
