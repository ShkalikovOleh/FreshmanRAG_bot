from typing import AsyncIterator, Dict, Iterator, List, Optional, Sequence, Tuple

from langchain_community.storage import SQLStore
from langchain_core.documents import Document
from sqlalchemy import Column, and_, delete, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class LangchainDocumentsStores(Base):
    __tablename__ = "langchain_docs_stores"

    key: Mapped[str] = mapped_column(primary_key=True, index=True, unique=True)
    namespace: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    page_content: Mapped[str] = mapped_column(nullable=False)
    cmetadata = Column(JSONB, nullable=True)


class SQLDocStore(SQLStore):
    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    async def acreate_schema(self) -> None:
        assert isinstance(self.engine, AsyncEngine)
        async with self.engine.begin() as session:
            await session.run_sync(Base.metadata.create_all)

    def drop(self) -> None:
        Base.metadata.drop_all(bind=self.engine.connect())

    async def amget(self, keys: Sequence[str]) -> List[Optional[Document]]:
        assert isinstance(self.engine, AsyncEngine)
        result: Dict[str, Document] = {}
        async with self._make_async_session() as session:
            stmt = select(LangchainDocumentsStores).filter(
                and_(
                    LangchainDocumentsStores.key.in_(keys),
                    LangchainDocumentsStores.namespace == self.namespace,
                )
            )
            for v in await session.scalars(stmt):
                result[v.key] = Document(
                    page_content=v.page_content, metadata=v.cmetadata
                )
        return [result.get(key) for key in keys]

    def mget(self, keys: Sequence[str]) -> List[Optional[Document]]:
        result = {}

        with self._make_sync_session() as session:
            stmt = select(LangchainDocumentsStores).filter(
                and_(
                    LangchainDocumentsStores.key.in_(keys),
                    LangchainDocumentsStores.namespace == self.namespace,
                )
            )
            for v in session.scalars(stmt):
                result[v.key] = Document(
                    page_content=v.page_content, metadata=v.cmetadata
                )
        return [result.get(key) for key in keys]

    async def amset(self, key_docs: Sequence[Tuple[str, Document]]) -> None:
        async with self._make_async_session() as session:
            await self._amdelete([key for key, _ in key_docs], session)
            session.add_all(
                [
                    LangchainDocumentsStores(
                        namespace=self.namespace,
                        key=k,
                        page_content=doc.page_content,
                        cmetadata=doc.metadata,
                    )
                    for k, doc in key_docs
                ]
            )
            await session.commit()

    def mset(self, key_docs: Sequence[Tuple[str, Document]]) -> None:
        values: Dict[str, Document] = dict(key_docs)
        with self._make_sync_session() as session:
            self._mdelete(list(values.keys()), session)
            session.add_all(
                [
                    LangchainDocumentsStores(
                        namespace=self.namespace,
                        key=k,
                        page_content=doc.page_content,
                        cmetadata=doc.metadata,
                    )
                    for k, doc in key_docs
                ]
            )
            session.commit()

    def _mdelete(self, keys: Sequence[str], session: Session) -> None:
        stmt = delete(LangchainDocumentsStores).filter(
            and_(
                LangchainDocumentsStores.key.in_(keys),
                LangchainDocumentsStores.namespace == self.namespace,
            )
        )
        session.execute(stmt)

    async def _amdelete(self, keys: Sequence[str], session: AsyncSession) -> None:
        stmt = delete(LangchainDocumentsStores).filter(
            and_(
                LangchainDocumentsStores.key.in_(keys),
                LangchainDocumentsStores.namespace == self.namespace,
            )
        )
        await session.execute(stmt)

    def yield_keys(self, *, prefix: Optional[str] = None) -> Iterator[str]:
        with self._make_sync_session() as session:
            for v in session.query(LangchainDocumentsStores).filter(  # type: ignore
                LangchainDocumentsStores.namespace == self.namespace
            ):
                if str(v.key).startswith(prefix or ""):
                    yield str(v.key)
            session.close()

    async def ayield_keys(self, *, prefix: Optional[str] = None) -> AsyncIterator[str]:
        async with self._make_async_session() as session:
            stmt = select(LangchainDocumentsStores).filter(
                LangchainDocumentsStores.namespace == self.namespace
            )
            for v in await session.scalars(stmt):
                if str(v.key).startswith(prefix or ""):
                    yield str(v.key)
            await session.close()
