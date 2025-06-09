// This script will fix the Appointments.jsx file to match the backend response structure
const fs = require('fs');
const path = require('path');

// Path to the Appointments.jsx file
const appointmentsPath = path.join(__dirname, 'pages', 'Appointments.jsx');

// Read the file content
let content = fs.readFileSync(appointmentsPath, 'utf8');

// Fix the patient and doctor name access
content = content.replace(
  /appointment\.patient\.name/g, 
  'appointment.patient_name'
);

content = content.replace(
  /appointment\.doctor\.name/g, 
  'appointment.doctor_name'
);

// Write the updated content back to the file
fs.writeFileSync(appointmentsPath, content);

console.log("Fixed Appointments.jsx to match backend response structure");
