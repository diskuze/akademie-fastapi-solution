from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from diskuze.dependencies import AppContext
from diskuze.dependencies import Database
from diskuze.dependencies import get_auth_user
from diskuze.dependencies import get_database
from diskuze.models import User
from diskuze.schema import schema

app = FastAPI()

graphql_app = GraphQLRouter(schema, context_getter=AppContext)
app.include_router(graphql_app, prefix="/graphql")
