const { PrismaClient } = require('@prisma/client');

async function getHash() {
    const prisma = new PrismaClient();
    
    try {
        const user = await prisma.user.findUnique({
            where: { username: 'gzentall' },
            select: { username: true, passwordHash: true }
        });
        
        if (user) {
            console.log('Username:', user.username);
            console.log('Password Hash:', user.passwordHash);
        } else {
            console.log('User not found');
        }
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await prisma.$disconnect();
    }
}

getHash();

