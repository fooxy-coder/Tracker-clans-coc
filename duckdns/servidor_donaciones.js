const http = require('http');

// Datos de ejemplo
let donaciones = {
    "Clan Ejemplo": [
        { nombre: "Player1", donado: 1500, recibido: 800 },
        { nombre: "Player2", donado: 2000, recibido: 1200 },
        { nombre: "Player3", donado: 500, recibido: 2000 }
    ]
};

const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    
    if (req.url === '/') {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>🏰 Tracker CoC</title>
                <style>
                    body { font-family: Arial; margin: 40px; background: #1a1a1a; color: #fff; }
                    table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                    th, td { border: 1px solid #444; padding: 12px; }
                    th { background: #333; }
                    .high { background: #2d5a2d; }
                    .low { background: #5a2d2d; }
                </style>
            </head>
            <body>
                <h1>🏰 Tracker Donaciones CoC</h1>
                <h2>mitracker.duckdns.org:8080</h2>
                <table>
                    <tr><th>Jugador</th><th>Donado</th><th>Recibido</th><th>Balance</th></tr>
                    ${donaciones["Clan Ejemplo"].map(p => `
                        <tr class="${p.donado > 1000 ? 'high' : 'low'}">
                            <td>${p.nombre}</td>
                            <td>${p.donado}</td>
                            <td>${p.recibido}</td>
                            <td>${p.donado - p.recibido}</td>
                        </tr>
                    `).join('')}
                </table>
                <p>✅ Servidor funcionando: ${new Date().toLocaleString()}</p>
            </body>
            </html>
        `);
    } else if (req.url === '/api') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(donaciones, null, 2));
    } else {
        res.writeHead(404);
        res.end('404 - No encontrado');
    }
});

const PORT = 8000;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ Servidor iniciado en puerto ${PORT}`);
    console.log(`🌐 Acceso: http://mitracker.duckdns.org:${PORT}`);
    console.log(`📊 API: http://mitracker.duckdns.org:${PORT}/api`);
    console.log('Presiona Ctrl+C para detener');
});
