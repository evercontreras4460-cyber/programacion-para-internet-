from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def inicio():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gaming Hub API</title>

        <style>

        body{
            font-family: Arial;
            background: linear-gradient(135deg,#0f172a,#1e293b);
            color:white;
            text-align:center;
            padding:50px;
        }

        h1{
            font-size:55px;
            margin-bottom:10px;
        }

        p{
            font-size:20px;
            color:#cbd5f5;
        }

        .container{
            margin-top:50px;
        }

        .card{
            display:inline-block;
            background:#1e293b;
            width:250px;
            margin:20px;
            padding:20px;
            border-radius:15px;
            box-shadow:0px 10px 20px rgba(0,0,0,0.5);
        }

        .card img{
            width:100%;
            border-radius:10px;
        }

        </style>

    </head>

    <body>

        <h1>🎮 Gaming Hub API</h1>
        <p>Proyecto FastAPI - Ever Adael Contreras Pacheco</p>

        <div class="container">

            <div class="card">
                <img src="https://upload.wikimedia.org/wikipedia/en/0/0c/Witcher_3_cover_art.jpg">
                <h3>The Witcher 3</h3>
            </div>

            <div class="card">
                <img src="https://upload.wikimedia.org/wikipedia/en/a/a7/Elden_Ring_Box_art.jpg">
                <h3>Elden Ring</h3>
            </div>

            <div class="card">
                <img src="https://upload.wikimedia.org/wikipedia/en/6/6e/Red_Dead_Redemption_II.jpg">
                <h3>Red Dead Redemption 2</h3>
            </div>

        </div>

    </body>
    </html>
    """