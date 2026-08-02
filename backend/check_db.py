import asyncio, sys
sys.path.append('.')
from app.core.database import AsyncSessionLocal
from app.models import Transaction, User
from sqlalchemy import select

async def main():
    db = AsyncSessionLocal()
    user = (await db.execute(select(User))).scalar_one()
    txs = (await db.execute(select(Transaction).where(Transaction.user_id == user.id))).scalars().all()
    print('Txs:', len(txs))
    await db.close()

if __name__ == '__main__':
    asyncio.run(main())
