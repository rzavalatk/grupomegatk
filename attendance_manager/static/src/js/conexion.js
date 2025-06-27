import sql from 'mssql';

const sql = require("mssql");

const config = {
    user: "sa",
    password: "M3g@tK2012",
    server: "192.168.10.12",
    database: "Megatk_Sistema",
    options: {
        encrypt: true,
        trustServerCertificate: true,
    },
    port: 1433,
};

async function queryDatabase() {
    try {
        const pool = await sql.connect(config);
        const result = await pool.request().query("SELECT * FROM users");
        
        // Convertir los resultados a JSON para enviarlos a Python
        console.log(JSON.stringify(result.recordset));
        process.exit(0); // Salir con éxito
    } catch (err) {
        console.error("Error:", err.message);
        process.exit(1); // Salir con error
    }
}

// Ejecutar la consulta
queryDatabase();
