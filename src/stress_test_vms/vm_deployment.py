from gpc import gpc

vm_type = 'e2-medium'
vm_specs = [
    {
        'name':'stressservereu',
        'type':vm_type,
        'family':'ubuntu-2204-lts',
        'proj':'ubuntu-os-cloud',
        'zone':'us-west1-a'
    },
    {
        'name':'stressserverus',
        'type':vm_type,
        'family':'ubuntu-2204-lts',
        'proj':'ubuntu-os-cloud',
        'zone':'europe-west3-a'
    },
    {
        'name':'stressserverasia',
        'type':vm_type,
        'family':'ubuntu-2204-lts',
        'proj':'ubuntu-os-cloud',
        'zone':'europe-west3-a'
    }
]

vm_metadata = [
    {'key':'init_stress','value':open('./stress_test_Init.py','r').read()},
    {'key':'init_pb2','value':open('../protobufs/workerInit_pb2.py','r').read()},
    {'key':'init_grpc','value':open('../protobufs/workerInit_pb2_grpc.py','r').read()},
    {'key':'lookup_stress','value':open('./stress_test_lookup.py','r').read()},
    {'key':'lookup_pb2','value':open('../protobufs/workerLookup_pb2.py','r').read()},
    {'key':'lookup_grpc','value':open('../protobufs/workerLookup_pb2_grpc.py','r').read()},
    {'key':'roll_stress','value':open('./stress_test_roll.py','r').read()},
    {'key':'roll_pb2','value':open('../protobufs/workerRoll_pb2.py','r').read()},
    {'key':'roll_grpc','value':open('../protobufs/workerRoll_pb2_grpc.py','r').read()},
    {'key':'char_stress','value':open('./stress_test_char.py','r').read()},
    {'key':'char_pb2','value':open('../protobufs/workerChar_pb2.py','r').read()},
    {'key':'char_grpc','value':open('../protobufs/workerChar_pb2_grpc.py','r').read()},
    {'key':'auth_token','value':open('./auth_token.json','r').read()}
]

g = gpc(
    project='',
    zone='',
    bucket=''
)

# create firewall rules if needed...

for vm in vm_specs:

    op = g.create_instance(
        name = vm['name'],
        #snap='lab6-snap', #make a new snapshot for the deployment...maybe pre-install/configure everything
        img_family=vm['family'],
        img_project=vm['proj'],
        vm_type=vm['type'],
        zone=vm['zone'],
        metadata=vm_metadata,
        startup='stress_test_startup.sh' #update this
    )
    g.wait_for_op(op['name'])

    g.apply_fw_tag(
        targ_instances=vm['name'],
        tags=['allow-lab6']  #update
    )

    