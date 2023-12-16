import mysql.connector as mysql
import logging
from typing import Optional, Tuple, Union, List, Any

import src.config as config
from src.article import Article


logger = logging.getLogger(__name__)
logger.setLevel(config.LOGGING_LEVEL)


class DataBase:
    def _create_connection(self) -> mysql.MySQLConnection:
        try:
            return mysql.connect(user=config.DB_USER, password=config.DB_PASS,
                                 host=config.DB_HOST, port=config.DB_PORT, database=config.DB_NAME)
        except mysql.errors.DatabaseError as err:
            logger.error(f"Database error: {err}")
            return self._create_connection()

    def _execute_sql(self, sql: str, items: Optional[Tuple] = None) -> None:
        if items is None:
            items = ()
        connection = None
        cursor = None
        try:
            connection = self._create_connection()
            cursor = connection.cursor(prepared=True)
            cursor.execute(sql, items)
            connection.commit()
        finally:
            if connection is not None:
                if connection.is_connected():
                    if cursor is not None:
                        cursor.close()
                    connection.close()

    def _retrieve_sql(self,
                      sql: str,
                      items: Optional[Tuple] = None,
                      fetch_all: bool = False) -> Optional[Union[List, Any]]:
        if items is None:
            items = ()
        connection = None
        cursor = None
        try:
            connection = self._create_connection()
            cursor = connection.cursor(prepared=True)
            cursor.execute(sql, items)
            if fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.fetchone()
            return result
        except mysql.Error as error:
            logger.error(f"Error while retrieving from database: {error}")
        finally:
            if connection is not None:
                if connection.is_connected():
                    if cursor is not None:
                        cursor.close()
                    connection.close()

    def add_article(self, article: Article) -> int:
        logger.info(f"Adding article to database: {article.url} from {article.origin}")
        items = (
            article.url, article.time, article.origin
        )
        self._execute_sql("INSERT INTO articles (url, time, origin) "
                          "VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE id = id", items)
        return self._retrieve_sql("SELECT id FROM articles WHERE url = %s", (article.url,))[0]
