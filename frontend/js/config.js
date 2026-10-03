/**
 * NyayaPath frontend configuration.
 * Override before loading any module, e.g. in a <script> tag:  window.NYAYAPATH_API_BASE = 'https://api.example.com'
 *
 * DEV_AUTO_LOGIN: no login UI exists in this phase. Most Django endpoints require a JWT, so in development the
 * client silently signs in with the demo user created by `python manage.py seed_demo_data`.
 * Set to false (and remove the credentials) in production; real authentication will be added later.
 */
export default {
  API_BASE: (window.NYAYAPATH_API_BASE ?? '') + '/api/v1',
  DEV_AUTO_LOGIN: window.NYAYAPATH_DEV_AUTO_LOGIN !== false,
  DEV_EMAIL: 'demo@nyayapath.local',
  DEV_PASSWORD: 'DemoPass#12345',
};
