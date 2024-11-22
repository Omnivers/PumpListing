import asyncio
import websockets
import json
import requests
from datetime import datetime, timezone
import time

class TokenMonitor:
    def __init__(self):
        self.websocket_uri = "wss://pumpportal.fun/api/data"
        self.processed_tokens = set()

    def format_token_info(self, token_data):
        """Format token information from websocket data"""
        try:
            # Conversion SOL en USD (prix approximatif)
            sol_price = 100  # À ajuster selon le prix actuel de SOL
            
            # Calculs
            market_cap_usd = token_data.get('marketCapSol', 0) * sol_price
            liquidity_usd = token_data.get('vSolInBondingCurve', 0) * sol_price
            
            return {
                'name': token_data.get('name', 'Unknown'),
                'symbol': token_data.get('symbol', 'Unknown'),
                'mint_address': token_data.get('mint', ''),
                'chain': 'Solana',
                'initial_buy': token_data.get('initialBuy', 0),
                'market_cap_sol': token_data.get('marketCapSol', 0),
                'market_cap_usd': market_cap_usd,
                'liquidity_sol': token_data.get('vSolInBondingCurve', 0),
                'liquidity_usd': liquidity_usd,
                'tokens_in_curve': token_data.get('vTokensInBondingCurve', 0),
                'creator': token_data.get('traderPublicKey', ''),
                'tx_signature': token_data.get('signature', ''),
                'uri': token_data.get('uri', ''),
                'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            }

        except Exception as e:
            print(f"Erreur de formatage: {e}")
            return None

    def print_token_info(self, token_data):
        """Affiche les informations du token"""
        if not token_data:
            return

        print("\n" + "="*60)
        print(f"🔥 NOUVEAU TOKEN SOLANA DÉTECTÉ 🔥")
        print(f"Nom: {token_data['name']} ({token_data['symbol']})")
        print(f"Mint Address: {token_data['mint_address']}")
        print(f"Market Cap: {token_data['market_cap_sol']:.3f} SOL (${token_data['market_cap_usd']:,.2f})")
        print(f"Liquidité: {token_data['liquidity_sol']:.3f} SOL (${token_data['liquidity_usd']:,.2f})")
        print(f"Initial Buy: {token_data['initial_buy']:,.0f} tokens")
        print(f"Tokens in Curve: {token_data['tokens_in_curve']:,.0f}")
        print(f"Créateur: {token_data['creator']}")
        print(f"Transaction: {token_data['tx_signature']}")
        print(f"Metadata URI: {token_data['uri']}")
        print(f"Créé le: {token_data['created_at']}")
        print("="*60 + "\n")

    async def monitor_tokens(self):
        """Monitore les nouveaux tokens en temps réel"""
        while True:
            try:
                async with websockets.connect(self.websocket_uri) as websocket:
                    print("🔌 Connecté au websocket. En attente de nouveaux tokens...")
                    
                    # Souscription aux événements
                    await websocket.send(json.dumps({"method": "subscribeNewToken"}))
                    
                    while True:
                        # Réception des événements websocket
                        message = await websocket.recv()
                        token_data = json.loads(message)
                        
                        # Ignorer le message de confirmation de souscription
                        if 'message' in token_data and 'Successfully subscribed' in token_data['message']:
                            continue
                            
                        # Vérifier si c'est un nouveau token
                        mint_address = token_data.get('mint')
                        if not mint_address or mint_address in self.processed_tokens:
                            continue
                            
                        self.processed_tokens.add(mint_address)
                        
                        # Formater et afficher les informations
                        token_info = self.format_token_info(token_data)
                        if token_info:
                            self.print_token_info(token_info)

            except websockets.exceptions.ConnectionClosed:
                print("❌ Connexion perdue. Tentative de reconnexion dans 5 secondes...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"❌ Erreur: {e}")
                await asyncio.sleep(5)

async def main():
    monitor = TokenMonitor()
    await monitor.monitor_tokens()

if __name__ == "__main__":
    asyncio.run(main())