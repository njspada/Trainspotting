import database_config

cnx = database_config.connection()

if cnx:
    print('connected')

cnx.close()


