"""Build the Vercel frontend; local Flask mode remains available via app.py."""
import json
import shutil
import tempfile
from pathlib import Path
from app import create_app

out=Path('dist');out.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
    app=create_app({'TESTING':True,'DATABASE':folder+'/build.sqlite3'})
    html=app.test_client().get('/').text
html=html.replace('<script src="/static/app.js" defer></script>', '<script src="/supabase.js" defer></script><script src="/cloud.js" defer></script><script src="/static/app.js" defer></script>')
html=html.replace('Stored on this device','Saved to your account').replace('Campus Wallet · Flask + SQLite','Campus Wallet · Personal expense tracker')
html=html.replace('</head>', '<style>body:not(.signed-in)>aside,body:not(.signed-in)>main{display:none}#login-card{max-width:420px;margin:10vh auto;padding:30px;background:white;border:1px solid #e5eae7;border-radius:16px}#login-card button{margin-top:12px}#auth-msg{color:#a63232;line-height:1.5}#sign-out{position:fixed;bottom:12px;left:20px;z-index:3}body.signed-in #login-card{display:none}body:not(.signed-in) #sign-out{display:none}</style></head>')
html=html.replace('</body>', '''<section id="login-card"><h1>Campus Wallet</h1><p class="muted">Sign in to keep your expenses private and saved across devices.</p><form id="login-form"><label>Email<input type="email" name="email" required autocomplete="email"></label><label>Password<input type="password" name="password" required minlength="8" autocomplete="current-password"></label><button class="primary full" type="submit">Sign in</button><button class="full" id="sign-up" type="button">Create account</button><p id="auth-msg" role="status"></p></form></section><button id="sign-out">Sign out</button></body>''')
(out/'index.html').write_text(html)
shutil.copytree('static',out/'static',dirs_exist_ok=True)
for name in ['supabase.js','cloud.js']:shutil.copyfile(name,out/name)
print('Built dist/ for Vercel with Supabase authentication and persistence.')
