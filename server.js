const http = require('http');
const frases = [
    "El éxito empieza con un primer paso.",
    "Nunca te rindas.",
    "Cada día es una nueva oportunidad.",
    "Eres más capaz de lo que crees.",
    "La disciplina supera al talento."
];


const server = http.createServer((req, res) => {;

    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });

    const fraseAleatoria = frases[Math.floor(Math.random() * frases.length)];

    res.end(`
    <html>
      <head>
        <title>Mi Proyecto Node</title>
        <style>
          body {
            background-color: #1e1e2f;
            color: white;
            font-family: Arial;
            text-align: center;
            padding-top: 100px;
          }
          h1 {
            color: #00ffcc;
          }
          button {
            padding: 10px 20px;
            font-size: 16px;
            background-color: #00ffcc;
            border: none;
            border-radius: 5px;
            cursor: pointer;
          }
        </style>
      </head>
      <body>
        <h1>Hola pa 🚀</h1>
        <p>Tu aplicación con Node.js está funcionando correctamente.</p>
        <p>${fraseAleatoria}</p>

        <button onclick="alert('¡Eres un crack programando! 😎')">
          Haz clic aquí
        </button>
      </body>
    </html>
  `);
});

server.listen(3000, () => {
    console.log('Servidor funcionando en http://localhost:3000');
});