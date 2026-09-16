import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import User, BankAccount, Transaction, Category

async def inspect():
    async with AsyncSessionLocal() as db:
        users = (await db.execute(select(User))).scalars().all()
        print(f"Users: {[u.email for u in users]}")
        for user in users:
            accs = (await db.execute(select(BankAccount).where(BankAccount.user_id == user.id))).scalars().all()
            print(f"  Accounts for {user.email}: {len(accs)}")
            txs = (await db.execute(select(Transaction).where(Transaction.user_id == user.id))).scalars().all()
            print(f"  Transactions for {user.email}: {len(txs)}")

if __name__ == "__main__":
    asyncio.run(inspect())
