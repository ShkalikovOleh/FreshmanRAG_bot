import os

import hydra
from omegaconf import DictConfig
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from bot.db import Admin, Base


@hydra.main(version_base="1.3", config_path="../configs", config_name="default")
def main(config: DictConfig) -> None:
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
        print("Database has been already created and initialized!")


if __name__ == "__main__":
    main()
