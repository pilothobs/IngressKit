import typer
from pathlib import Path
from .repair import Repairer, Schema

app = typer.Typer(add_completion=False)


@app.command()
def main(
    in_: Path = typer.Option(..., "--in", help="Input CSV file"),
    out: Path = typer.Option(..., "--out", help="Output cleaned CSV file"),
    schema: str = typer.Option("contacts", help="Target schema: contacts|transactions|products"),
    tenant_id: str = typer.Option("default", help="Tenant identifier for episodic memory (placeholder)"),
):
    schemas = {
        "contacts": Schema.contacts(),
        "transactions": Schema.transactions(),
        "products": Schema.products(),
    }
    if schema not in schemas:
        typer.echo(f"Unknown schema: {schema}")
        raise typer.Exit(code=1)

    r = Repairer(schema=schemas[schema], tenant_id=tenant_id)
    result = r.repair_file(in_)
    result.save(out)
    typer.echo(f"Repaired {result.summary['rows_in']} rows -> {result.summary['rows_out']} rows")
    typer.echo(f"Sample diffs: {result.sample_diffs}")


if __name__ == "__main__":
    app()


