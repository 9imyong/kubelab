import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || '30s',
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:18080';

export default function () {
  const payload = JSON.stringify({
    ts: Date.now(),
    value: Math.random(),
  });

  const res = http.post(`${BASE_URL}/jobs`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(res, {
    'post jobs status is 200': (r) => r.status === 200,
    'has job_id': (r) => r.json('job_id') !== null,
  });

  sleep(0.2);
}
