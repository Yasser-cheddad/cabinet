web: gunicorn backend.cabinet.wsgi --log-file -
release: cd frontend && npm install && npm run build
heroku config:set TWILIO_ACCOUNT_SID=AC941bf7f1f9a4b40155186adc1585bf93
heroku config:set TWILIO_AUTH_TOKEN=f9c608fd6bf5947b7eadf847bf058877
heroku config:set OPENROUTER_API_KEY=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