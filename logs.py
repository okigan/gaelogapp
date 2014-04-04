import time
import json

import webapp2
from google.appengine.api.logservice import logservice


class LogPage(webapp2.RequestHandler):
    def get(self):
        end_date = self.request.get('end_date', None)
        end_time = self.request.get('end_time', None)

        start_date = self.request.get('start_date', None)
        start_time = self.request.get('start_time', None)
        count = self.request.get('count', None)
        offset = None

        end_time = time.time() if end_time is None else float(end_time)
        count = None if count is None else int(count)

        if end_date:
            end_time = time.mktime(time.strptime(end_date, "%Y%m%d"))

        if start_date:
            start_time = time.mktime(time.strptime(start_date, "%Y%m%d"))

        class MagicEncoder(json.JSONEncoder):
            def default(self, obj):
                use_dict = [logservice.AppLog, logservice.log_service_pb.RequestLog,
                            logservice.log_service_pb.LogLine, logservice.log_service_pb.LogOffset]
                skip = [logservice.RequestLog]
                if any(isinstance(obj, x) for x in use_dict):
                    return obj.__dict__
                elif any(isinstance(obj, x) for x in skip):
                    o = {}
                    attributes = [
                        'api_mcycles',
                        'app_engine_release',
                        'app_id',
                        'app_logs',
                        'combined',
                        'cost',
                        'end_time',
                        'finished',
                        'host',
                        'http_version',
                        'instance_key',
                        'ip',
                        'latency',
                        'mcycles',
                        'method',
                        'module_id',
                        'nickname',
                        'offset',
                        'pending_time',
                        'referrer',
                        'replica_index',
                        'request_id',
                        'resource',
                        'response_size',
                        'start_time',
                        'status',
                        'task_name',
                        'task_queue_name',
                        'url_map_entry',
                        'user_agent',
                        'version_id',
                        'was_loading_request']

                    for a in attributes:
                        f = getattr(obj, a)
                        if f:
                            if callable(f):
                                o[a] = f()
                            else:
                                o[a] = f
                    return o
                elif 'Lock' in str(type(obj)):
                    return {}
                else:
                    return json.JSONEncoder.default(self, obj)

        #wish json could stream, till then this will hog RAM
        log_records = []
        log_records_gen = logservice.fetch(end_time=end_time,
                                           offset=offset,
                                           minimum_log_level=logservice.LOG_LEVEL_INFO,
                                           include_app_logs=True)

        counter = 0
        for idx, log_record in enumerate(log_records_gen):
            if start_time and log_record.start_time < start_time:
                continue

            log_records.append(log_record)

            if count and counter >= count:
                break

            counter += 1

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(log_records, indent=True, cls=MagicEncoder))


app = webapp2.WSGIApplication(
    [('/admin/logs', LogPage)],
    debug=True
)


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    webapp2.util.run_wsgi_app(app)


if __name__ == '__main__':
    main()