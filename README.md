# IT Academy

This is a full solution to IT Academy FastAPI project.

## Running the DB locally

```sh
docker-compose up database
mysql -uroot -proot -h127.0.0.1 diskuze < utils/db/db.sql
mysql -uroot -proot -h127.0.0.1 diskuze < utils/db/discussion.sql
mysql -uroot -proot -h127.0.0.1 diskuze < utils/db/user.sql
mysql -uroot -proot -h127.0.0.1 diskuze < utils/db/comment.sql
```
