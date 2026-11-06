import asyncio
import websockets
import json
import time
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

async def test_live_edge_combat():
    url_base = 'wss://poker-chess-server.laurence5kg.workers.dev'
    room_id = f'live_combat_{int(time.time())}'
    print(f'Starting Live Production Edge Combat Test on room {room_id}...')

    async with websockets.connect(f'{url_base}/room/{room_id}') as ws_host:
        await ws_host.send(json.dumps({
            'v': 1,
            'type': 'create_room',
            'payload': {'roomId': room_id, 'hostNickname': 'HostRed', 'sidePreference': 'red'}
        }))
        h_join = json.loads(await ws_host.recv())
        print('1. Host connected:', h_join['payload']['playerColor'])
        host_token = h_join['payload']['sessionToken']

        async with websockets.connect(f'{url_base}/room/{room_id}') as ws_guest:
            await ws_guest.send(json.dumps({
                'v': 1,
                'type': 'join_room',
                'payload': {'roomId': room_id, 'nickname': 'GuestBlack'}
            }))
            g_join = json.loads(await ws_guest.recv())
            print('2. Guest connected:', g_join['payload']['playerColor'])
            guest_token = g_join['payload']['sessionToken']

            # Receive setup_start
            h_start = json.loads(await ws_host.recv())
            g_start = json.loads(await ws_guest.recv())
            print('3. setup_start received on both clients.')

            # Red deployment:
            # Put Officer 9 at frontline (4, 2)
            camp_red = [{'r': r, 'c': c, 'rank': '2', 'suit': '♥'} for r in range(5) for c in range(5)]
            res_red = [{'rank': 'K', 'suit': '♥'}, {'rank': '10', 'suit': '♥'}]
            camp_red[0]['rank'] = 'JOKER' # (0, 0)
            camp_red[1]['rank'] = 'Q'     # (0, 1)
            camp_red[2]['rank'] = 'J'     # (0, 2)
            camp_red[3]['rank'] = 'Q'     # (0, 3)
            camp_red[4]['rank'] = 'J'     # (0, 4)
            # Frontline piece at (4, 2): Red Officer 9
            camp_red[22]['rank'] = '9'

            # Black deployment:
            # Put Officer 7 at frontline (7, 2)
            camp_black = [{'r': r, 'c': c, 'rank': '2', 'suit': '♠'} for r in range(7, 12) for c in range(5)]
            res_black = [{'rank': 'K', 'suit': '♠'}, {'rank': '10', 'suit': '♠'}]
            camp_black[20]['rank'] = 'JOKER' # (11, 0)
            camp_black[21]['rank'] = 'Q'     # (11, 1)
            camp_black[22]['rank'] = 'J'     # (11, 2)
            camp_black[23]['rank'] = 'Q'     # (11, 3)
            camp_black[24]['rank'] = 'J'     # (11, 4)
            # Frontline piece at (7, 2): Black Officer 7
            camp_black[2]['rank'] = '7'

            # Submit setups
            print('4. Submitting layouts...')
            await ws_host.send(json.dumps({
                'v': 1, 'type': 'submit_layout',
                'payload': {'camp': camp_red, 'reserves': res_red, 'sessionToken': host_token, 'playerColor': 'red'}
            }))
            h_conf = json.loads(await ws_host.recv())
            assert h_conf['type'] == 'setup_confirmed'

            await ws_guest.send(json.dumps({
                'v': 1, 'type': 'submit_layout',
                'payload': {'camp': camp_black, 'reserves': res_black, 'sessionToken': guest_token, 'playerColor': 'black'}
            }))
            g_conf = json.loads(await ws_guest.recv())
            assert g_conf['type'] == 'setup_confirmed'

            # Initial state_view
            h_state = json.loads(await ws_host.recv())
            g_state = json.loads(await ws_guest.recv())
            print('5. Match transitioned to state:', h_state['payload']['gameState'], 'Turn:', h_state['payload']['currentTurn'])

            # Move sequence towards clash:
            # Turn 1 (Red): Move (4, 2) -> (5, 2)
            print('6. Turn 1 (Red): Advancing Officer 9 from (4, 2) to (5, 2)...')
            await ws_host.send(json.dumps({
                'v': 1, 'type': 'action',
                'payload': {'type': 'move', 'from': {'r': 4, 'c': 2}, 'to': {'r': 5, 'c': 2}, 'sessionToken': host_token, 'playerColor': 'red'}
            }))
            h_act1 = json.loads(await ws_host.recv())
            g_act1 = json.loads(await ws_guest.recv())
            print('   Turn 1 action_result: clash is', h_act1['payload'].get('clash'))
            assert h_act1['payload']['clash'] is None, 'Non-combat move should have clash: None'

            h_s1 = json.loads(await ws_host.recv())
            g_s1 = json.loads(await ws_guest.recv())
            print('   Turn 1 completed. Current turn now:', h_s1['payload']['currentTurn'])
            assert h_s1['payload']['currentTurn'] == 'black'

            # Turn 2 (Black): Move (7, 2) -> (6, 2)
            print('7. Turn 2 (Black): Advancing Officer 7 from (7, 2) to (6, 2)...')
            await ws_guest.send(json.dumps({
                'v': 1, 'type': 'action',
                'payload': {'type': 'move', 'from': {'r': 7, 'c': 2}, 'to': {'r': 6, 'c': 2}, 'sessionToken': guest_token, 'playerColor': 'black'}
            }))
            h_act2 = json.loads(await ws_host.recv())
            g_act2 = json.loads(await ws_guest.recv())
            print('   Turn 2 action_result: clash is', h_act2['payload'].get('clash'))
            assert h_act2['payload']['clash'] is None, 'Non-combat move should have clash: None'

            h_s2 = json.loads(await ws_host.recv())
            g_s2 = json.loads(await ws_guest.recv())
            print('   Turn 2 completed. Current turn now:', h_s2['payload']['currentTurn'])
            assert h_s2['payload']['currentTurn'] == 'red'

            # Turn 3 (Red ATTACKS Black): Red at (5, 2) ATTACKS Black at (6, 2) -> CLASH!
            print('8. Turn 3 (Red ATTACKS Black): Red Officer 9 at (5, 2) clashes with Black at (6, 2)...')
            await ws_host.send(json.dumps({
                'v': 1, 'type': 'action',
                'payload': {'type': 'move', 'from': {'r': 5, 'c': 2}, 'to': {'r': 6, 'c': 2}, 'sessionToken': host_token, 'playerColor': 'red'}
            }))

            h_clash_act = json.loads(await ws_host.recv())
            g_clash_act = json.loads(await ws_guest.recv())
            clash = h_clash_act['payload']['clash']
            print('9. CLASH RESULT RECEIVED ON HOST AND GUEST!')
            print('   Attacker:', clash['attacker'])
            print('   Defender:', clash['defender'])
            print('   Winner:', clash['winner'])
            print('   Sound:', clash['sound'])
            print('   Outcome Text:', clash['outcomeText'])

            # Assertions for complete clash parity
            assert clash is not None, 'Clash payload must exist!'
            assert clash['attacker']['rank'] == '9', 'Attacker rank should be 9'
            assert clash['attacker']['roleName'] == 'Officer', 'Attacker roleName should be Officer'
            assert clash['defender']['rank'] == '7', 'Defender rank should be 7'
            assert clash['defender']['roleName'] == 'Officer', 'Defender roleName should be Officer'
            assert clash['winner'] == 'attacker', 'Attacker (9) should defeat Defender (7)'
            assert clash['sound'] == 'clash', 'Sound must be clash'

            # Next message: state_view
            h_s3 = json.loads(await ws_host.recv())
            g_s3 = json.loads(await ws_guest.recv())
            print('10. Post-combat state_view received!')
            survivor = h_s3['payload']['board'][6][2]
            print('   Square (6, 2) occupied by:', survivor)
            assert survivor is not None and survivor['player'] == 'red', 'Red winner must occupy (6, 2)'
            print('   Red mochigoma length:', len(h_s3['payload']['hands']['red']['mochigoma']))
            assert len(h_s3['payload']['hands']['red']['mochigoma']) == 1, 'Defeated Black 7 captured into Red mochigoma'

            print('\n================================================================')
            print('🎉 LIVE PRODUCTION CLASH TEST VERIFIED 100% ON CLOUDFLARE EDGE!')
            print('================================================================')

if __name__ == '__main__':
    asyncio.run(test_live_edge_combat())
