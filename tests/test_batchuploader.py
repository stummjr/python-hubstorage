"""
Test Project
"""
import time
from collections import defaultdict
from hstestcase import HSTestCase
from hubstorage import ItemTooLarge


class BatchUploaderTest(HSTestCase):

    def _job_and_writer(self, **writerargs):
        self.project.push_job(self.spidername)
        job = self.project.start_job()
        bu = self.hsclient.batchuploader
        w = bu.create_writer(job.items.url, auth=self.auth, **writerargs)
        return job, w

    def test_writer_batchsize(self):
        job, w = self._job_and_writer(size=10)
        for x in xrange(111):
            w.write({'x': x})

        w.close()
        groups = defaultdict(int)
        for doc in job.items.list(meta=['_ts']):
            groups[doc['_ts']] += 1

        self.assertEqual(len(groups), 12)

    def test_writer_maxitemsize(self):
        job, w = self._job_and_writer()
        m = w.maxitemsize
        self.assertRaises(ItemTooLarge, w.write, {'b': 'x' * m})
        self.assertRaises(ItemTooLarge, w.write, {'b'*m: 'x'})
        self.assertRaises(ItemTooLarge, w.write, {'b'*(m/2): 'x'*(m/2)})

    def test_writer_contentencoding(self):
        for ce in ('identity', 'gzip'):
            job, w = self._job_and_writer(content_encoding=ce)
            for x in xrange(111):
                w.write({'x': x})
            w.close()
            self.assertEqual(job.items.stats()['totals']['input_values'], 111)

    def test_writer_interval(self):
        job, w = self._job_and_writer(size=1000, interval=1)
        for x in xrange(111):
            w.write({'x': x})
            if x == 50:
                time.sleep(2)

        w.close()
        groups = defaultdict(int)
        for doc in job.items.list(meta=['_ts']):
            groups[doc['_ts']] += 1

        self.assertEqual(len(groups), 2)