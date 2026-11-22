from aplicacion import crear_app

app = crear_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
