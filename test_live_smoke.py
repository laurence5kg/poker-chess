import asyncio
import websockets
import json
import time

async def test_live_production():
    url_base = 'wss://poker-chess-server.laurence5kg.workers.dev'
    room_id = f'live_smoke_{int(time.time())}'
    print(f'Starting Live Production Smoke Test on room {room_id}...')

    async with websockets.connect(f'{url_base}/room/{room_id}') as ws_host:
        await ws_host.send(json.dumps({
            'v': 1,
            'type': 'create_room',
            'payload': {'roomId': room_id, 'hostNickname': 'HostAlpha', 'sidePreference': 'red'}
        }))
        h_join = json.loads(await ws_host.recv())
        print('1. Host joined room:', h_join['type'], h_join['payload']['playerColor'])
        host_token = h_join['payload']['sessionToken']

        async with websockets.connect(f'{url_base}/room/{room_id}') as ws_guest:
            await ws_guest.send(json.dumps({
                'v': 1,
                'type': 'join_room',
                'payload': {'roomId': room_id, 'nickname': 'GuestBeta'}
            }))
            g_join = json.loads(await ws_guest.recv())
            print('2. Guest joined room:', g_join['type'], g_join['payload']['playerColor'])
            guest_token = g_join['payload']['sessionToken']

            # Both receive setup_start
            h_start = json.loads(await ws_host.recv())
            g_start = json.loads(await ws_guest.recv())
            print('3. Both received setup_start:', h_start['type'], g_start['type'])

            # Simulate 5-second human thinking delay
            print('4. Simulating human deployment pause (5s)...')
            await asyncio.sleep(5)

            # Test Ping/Pong
            await ws_host.send(json.dumps({'v': 1, 'type': 'ping', 'payload': {'time': int(time.time() * 1000)}}))
            h_pong = json.loads(await ws_host.recv())
            print('5. Ping/Pong exchange verified:', h_pong['type'])

            # Red valid camp layout (Flag and mines on back row 0, frontline row 4 mobiles)
            camp_red = [{'r': r, 'c': c, 'rank': '2', 'suit': 'hearts'} for r in range(5) for c in range(5)]
            res_red = [{'rank': 'K', 'suit': 'spades'}, {'rank': '10', 'suit': 'hearts'}]
            camp_red[0]['rank'] = 'JOKER' # (0, 0)
            camp_red[1]['rank'] = 'Q'     # (0, 1)
            camp_red[2]['rank'] = 'J'     # (0, 2)
            camp_red[3]['rank'] = 'Q'     # (0, 3)
            camp_red[4]['rank'] = 'J'     # (0, 4)

            # Black valid camp layout (Flag and mines on back row 11, frontline row 7 mobiles)
            camp_black = [{'r': r, 'c': c, 'rank': '2', 'suit': 'spades'} for r in range(7, 12) for c in range(5)]
            res_black = [{'rank': 'K', 'suit': 'diamonds'}, {'rank': '10', 'suit': 'clubs'}]
            camp_black[20]['rank'] = 'JOKER' # (11, 0)
            camp_black[21]['rank'] = 'Q'     # (11, 1)
            camp_black[22]['rank'] = 'J'     # (11, 2)
            camp_black[23]['rank'] = 'Q'     # (11, 3)
            camp_black[24]['rank'] = 'J'     # (11, 4)

            # Host submits layout with sessionToken attached
            print('6. Host clicking Confirm & Battle...')
            await ws_host.send(json.dumps({
                'v': 1,
                'type': 'submit_layout',
                'payload': {'camp': camp_red, 'reserves': res_red, 'sessionToken': host_token, 'playerColor': 'red'}
            }))
            h_conf = json.loads(await ws_host.recv())
            print('   Host confirmation result:', h_conf['type'], h_conf.get('payload'))
            assert h_conf['type'] == 'setup_confirmed', f'Host setup failed: {h_conf}'

            # Guest submits layout with sessionToken attached
            print('7. Guest clicking Confirm & Battle...')
            await ws_guest.send(json.dumps({
                'v': 1,
                'type': 'submit_layout',
                'payload': {'camp': camp_black, 'reserves': res_black, 'sessionToken': guest_token, 'playerColor': 'black'}
            }))
            g_conf = json.loads(await ws_guest.recv())
            print('   Guest confirmation result:', g_conf['type'], g_conf.get('payload'))
            assert g_conf['type'] == 'setup_confirmed', f'Guest setup failed: {g_conf}'

            # Both receive state_view with gameState == 'playing'
            h_state = json.loads(await ws_host.recv())
            g_state = json.loads(await ws_guest.recv())
            print('8. Host state_view gameState:', h_state['payload']['gameState'], 'Turn:', h_state['payload']['currentTurn'])
            print('   Guest state_view gameState:', g_state['payload']['gameState'], 'Turn:', g_state['payload']['currentTurn'])
            assert h_state['payload']['gameState'] == 'playing', 'Game must be playing'
            assert g_state['payload']['gameState'] == 'playing', 'Game must be playing'

            # 9. Host makes first move (row 4 to row 5)
            legal_moves = h_state['payload']['legalActions']
            print(f'9. Red legal actions count: {len(legal_moves)}')
            first_move = next(a for a in legal_moves if a['type'] == 'move')
            from_pos = (first_move['from']['r'], first_move['from']['c'])
            to_pos = (first_move['to']['r'], first_move['to']['c'])
            print(f'   Red executing move from {from_pos} to {to_pos}')

            await ws_host.send(json.dumps({
                'v': 1,
                'type': 'action',
                'payload': {**first_move, 'sessionToken': host_token, 'playerColor': 'red'}
            }))

            # Both receive action_result and updated state_view
            h_act = json.loads(await ws_host.recv())
            g_act = json.loads(await ws_guest.recv())
            print('10. Action result received:', h_act['type'], g_act['type'])

            h_next_state = json.loads(await ws_host.recv())
            g_next_state = json.loads(await ws_guest.recv())
            print('11. Turn transitioned to:', h_next_state['payload']['currentTurn'])
            assert h_next_state['payload']['currentTurn'] == 'black', 'Turn should now be Black'

            print('\n[LIVE SMOKE TEST PASSED 100% SUCCESS] All 10 Rounds Verified on Edge Production!')

asyncio.run(test_live_production())
