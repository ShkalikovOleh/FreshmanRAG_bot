import os

import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig, ListConfig
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from bot.db import Admin, Base


def init_admin_db(config: DictConfig) -> None:
    father_tg_id = os.getenv("FATHER_TG_ID")
    father_tg_tag = os.getenv("FATHER_TG_TAG")
    engine = create_engine(config["bot_db_connection"])

    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)

    try:
        with Session() as session:
            main_admin = Admin(
                tg_id=father_tg_id,
                tg_tag=father_tg_tag,
                can_add_info=True,
                can_add_new_admins=True,
                added_by_id=father_tg_id,
            )
            session.add(main_admin)
            session.commit()
    except IntegrityError:
        print("Admin database has been already created and initialized!")


def init_pgsql_docstore(store_config: DictConfig):
    docstore = instantiate(store_config, async_mode=False)
    docstore.create_schema()


# flake8: noqa: C901
def finditems(obj, key):
    found = []
    if isinstance(obj, (dict, DictConfig)):
        if key in obj:
            found.append(obj[key])
        for _, v in obj.items():
            if isinstance(v, (dict, DictConfig)):
                result = finditems(v, key)
                if result is not None:
                    found.extend(result)
            elif isinstance(v, (list, ListConfig)):
                for item in v:
                    result = finditems(item, key)
                    if result is not None:
                        found.extend(result)
    elif isinstance(obj, (list, ListConfig)):
        for item in obj:
            result = finditems(item, key)
            if result is not None:
                found.extend(result)
    return list(set(found))


@hydra.main(version_base="1.3", config_path="../configs", config_name="default")
def main(config: DictConfig) -> None:
    init_admin_db(config)

    docstore_cfgs = finditems(config, "docstore")
    for cfg in docstore_cfgs:
        if cfg["_target_"] == "crag.storage.PGSQLDocStore":
            init_pgsql_docstore(cfg)


if __name__ == "__main__":
    main()
