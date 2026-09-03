// Template: Jest tests (raw). Placeholders substituted by NodeTestGenerator.
const request = require('supertest');
const app = require('./__MODULE_NAME__');

describe('__MODULE_NAME__ API', () => {
  test('GET /healthz returns ok', async () => {
    const res = await request(app).get('/healthz');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('ok');
  });

  test('GET /api/v1/__ROUTE__ returns listing', async () => {
    const res = await request(app).get('/api/v1/__ROUTE__');
    expect(res.statusCode).toBe(200);
  });
});