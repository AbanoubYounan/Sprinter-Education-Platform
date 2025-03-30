const mysql = require('mysql2/promise');
const { DB_HOST, DB_NAME, DB_USER, DB_PASSWORD} = require('./index');

const pool = mysql.createPool({
  host: DB_HOST,
  user: DB_USER,
  password: DB_PASSWORD,
  database: DB_NAME,
});

// Function to execute queries
const quering = async (sql, params) => {
  const [results] = await pool.execute(sql, params);
  return results;
};

module.exports = quering;