import sqlite3
import os

# Caminho do banco (ajuste conforme sua estrutura)
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "producao.db")

print(f"🔍 Verificando banco em: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = [row[0] for row in cursor.fetchall()]
    print("\n=== TABELAS EXISTENTES ===")
    for tabela in tabelas:
        print(f"- {tabela}")
    
    # Contar registros na tabela 'producao'
    if "producao" in tabelas:
        cursor.execute("SELECT COUNT(*) FROM producao;")
        count = cursor.fetchone()[0]
        print(f"\n✅ Registros na tabela 'producao': {count}")
        
        # Mostrar exemplos de dados
        if count > 0:
            print("\n🔍 Primeiros registros:")
            cursor.execute("SELECT id, producao_id, data_producao FROM producao LIMIT 3;")
            for row in cursor.fetchall():
                print(f"ID: {row[0]} | Bloco: {row[1]} | Data: {row[2]}")
    else:
        print("\n❌ Tabela 'producao' não encontrada no banco")
    
    conn.close()

except Exception as e:
    print(f"\n❌ Erro ao acessar o banco: {str(e)}")
    print("💡 Verifique se o arquivo 'instance/producao.db' existe")