from prefect_flow import pipeline_macroentorno_ecuador


if __name__ == "__main__":
    pipeline_macroentorno_ecuador.serve(
        name="automatizacion-rpa",
        cron="0 */6 * * *"
    )