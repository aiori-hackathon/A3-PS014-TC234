# API notes

All routes are prefixed `/api`. Admin and agent endpoints use `Authorization: Bearer <token>` configured in backend environment. Never embed either token in the browser application.

`POST /participants` accepts displayName, city, area, isp, medium, connection, deviceInfo and `consent:true`. Medium enums: `FIBER`, `CELLULAR_4G`, `CELLULAR_5G`, `FIXED_WIRELESS`, `SATELLITE`, `OTHER`. Connection enums: `WIFI`, `ETHERNET`.

`POST /measurements` requires an enrolled participant id and explicit metric fields; nullable metric values are allowed. Include a conditions object with probe configuration. Source defaults to AGENT. Do not send fabricated demo measurements to the real API.

Admin routes: `GET /participants`, `PATCH /participants/:id`, `GET /measurements`, `GET /analytics/summary`, `GET|POST /schedules`, `POST /reports/export`.
