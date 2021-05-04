import asyncio

from databases import Database

database = Database('sqlite:///storage/data.db')


# async def main():
#     await database.connect()
#     # Create a table.
#     query = """CREATE TABLE HighScores (id INTEGER PRIMARY KEY, name VARCHAR(100), score INTEGER)"""
#     await database.execute(query=query)
#
#     # Insert some data.
#     query = "INSERT INTO HighScores(name, score) VALUES (:name, :score)"
#     values = [
#         {"name": "Daisy", "score": 92},
#         {"name": "Neil", "score": 87},
#         {"name": "Carol", "score": 43},
#     ]
#     await database.execute_many(query=query, values=values)
#     # Run a database query.
#     query = "SELECT * FROM HighScores"
#     rows = await database.fetch_all(query=query)
#
#     print('High Scores:', rows)
#
#
# asyncio.run(main())
