import os

# Buscar todos os arquivos producao.db no diretório atual e subdiretórios
print("🔍 Procurando arquivos 'producao.db'...\n")
for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
    for file in files:
        if file == "producao.db":
            caminho = os.path.join(root, file)
            print(f"📁 Encontrado: {caminho}")
            
            # Verificar quantos registros tem
            import sqlite3
            try:
                conn = sqlite3.connect(caminho)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM producao;")
                count = cursor.fetchone()[0]
                print(f"   ✅ Registros: {count}\n")
                conn.close()
            except:
                print("   ❌ Erro ao acessar\n")