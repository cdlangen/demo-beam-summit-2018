from __future__ import absolute_import

import logging
import re

import apache_beam as beam
from apache_beam.transforms import window
from apache_beam.transforms import trigger
from apache_beam.io.external.kafka import ReadFromKafka
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms.trigger import AccumulationMode


class LoggingDoFn(beam.DoFn):
    def process(self, element):
        logging.info(element)


def run():
    options = PipelineOptions([
        "--runner=PortableRunner",
        "--job_endpoint=localhost:8099",
        "--environment_type=LOOPBACK"
    ])
    # options = PipelineOptions([
    #     "--runner=FlinkRunner",
    #     "--flink_master=localhost:8081",
    # ])
    with beam.Pipeline(options=options) as p:
        (p | 'ReadFromKafka' >> ReadFromKafka(consumer_config={"bootstrap.servers": "localhost:9092"},
                                              topics=["beam-input"])
        | 'ExtractWords' >> beam.FlatMap(lambda kv: re.findall(r'[A-Za-z\']+', kv[1]))
        | 'Window' >> beam.WindowInto(window.GlobalWindows(), trigger=trigger.Repeatedly(trigger.AfterCount(1)),
                                      accumulation_mode=AccumulationMode.ACCUMULATING)
        | 'Count' >> beam.combiners.Count.PerElement()
        | 'Format' >> beam.Map(lambda word_count: '%s: %s' % (word_count[0], word_count[1]))
         | 'Log' >> beam.ParDo(LoggingDoFn()))

        # result = p.run()
        # result.wait_until_finish()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
    # import os
    #
    # print("{}:{}".format(os.getegid(), os.geteuid()))
