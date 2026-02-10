"""
사용법 참고:

DocPermissionRepository는 doc_recipe_member 테이블에 대한 DB 조회 및 관리를 담당함.
"""

from typing import List
from sqlalchemy import select, delete, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import DocRecipeMember


class DocPermissionRepository:
    """문서 권한 정보를 관리하는 저장소."""

    def __init__(self, db: AsyncSession):
        """DB 세션을 초기화함."""
        self.db = db
    
    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create_doc_permission(self, recipe_seq: int, user_seq: int, role_code: str) -> int:
        member = DocRecipeMember(recipe_seq=recipe_seq, user_seq=user_seq, role_code=role_code)

        self.db.add(member)
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return 1

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def read_all_doc_permissions(self):
        """현재 DB에 존재하는 모든 문서 권한 목록을 조회함. (문서명, 사용자명 포함)"""
        from common.models import DocRecipe, User
        
        stmt = (
            select(
                DocRecipeMember,
                DocRecipe.title.label('doc_name'),
                User.username.label('user_name')
            )
            .join(DocRecipe, DocRecipeMember.recipe_seq == DocRecipe.recipe_seq)
            .join(User, DocRecipeMember.user_seq == User.user_seq)
            .order_by(DocRecipeMember.recipe_seq, DocRecipeMember.user_seq)
        )
        
        result = await self.db.execute(stmt)
        
        # 결과를 (DocRecipeMember, doc_name, user_name) 튜플 리스트로 반환
        return list(result.all())


    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    async def update_doc_permission(self, recipe_seq: int, user_seq: int, role_code: str) -> int:
        """문서 권한 수정. 성공 시 1, 실패 시 0"""

        stmt = (update(DocRecipeMember).where(
                DocRecipeMember.recipe_seq == recipe_seq,
                DocRecipeMember.user_seq == user_seq,
            ).values(role_code=role_code))

        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount or 0


    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------
    async def delete_doc_permission(self, recipe_seq: int, user_seq: int):
        """해당 문서 권한을 DB에서 삭제"""
        stmt = delete(DocRecipeMember).where(DocRecipeMember.recipe_seq == recipe_seq, DocRecipeMember.user_seq == user_seq)
        await self.db.execute(stmt)
        await self.db.commit()
    

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------


