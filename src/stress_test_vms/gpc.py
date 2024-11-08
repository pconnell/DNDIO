import os, time, googleapiclient.discovery, google.auth
# import google.oauth2.service_account as service_account
# from pprint import pprint

class gpc():

    def __init__(
        self,
        project:str=None,
        zone:str=None,
        bucket:str=None,
    ):
        if project is not None:
            os.system("gcloud config set project {}".format(project))
        self.credentials, self.project = google.auth.default()
        self.compute = googleapiclient.discovery.build(
            'compute',
            'v1',
            credentials=self.credentials
        )
        self.proj_name = project
        self.zone = zone
        self.bucket = bucket

    def local_scp_transfer(
        self,
        local_file:str,
        instance_name:str,
        remote_dir:str,
        project:str=None,
        zone:str=None
    ):
        if isinstance(self.compute,googleapiclient.discovery.Resource):
            self.compute.instances()
            pass    
        pass

    def wait_for_op(
        self,
        op:str,
        project:str=None,
        zone:str=None
    ):
        if not project:
            project = self.project
        if not zone:
            zone = self.zone
        
        while True:
            result = (
                self.compute.zoneOperations()
                .get(project=project,zone=zone, operation=op)
                .execute()
            )
            if result['status'] == 'DONE':
                print("Operation {}: Done.".format(op))
                if "error" in result:
                    raise Exception(result['error'])
                return result
            time.sleep(1)

    def create_instance(
        self,
        name:str,
        img_family:str,
        img_project:str,
        vm_type:str,
        snap:str=None,
        startup:str='startup-script.sh',
        metadata:list=[],
        project:str=None,
        zone:str=None,
    ):
        if not project:
            project = self.project

        if not zone:
            zone = self.zone
        
        image_response = (
            self.compute.images()
            .getFromFamily(project=img_project,family=img_family)
            .execute()
        )

        source_disk_image = image_response['selfLink']
        
        # disk_init_params = {
        #     'sourceImage':source_disk_image
        # }

        disk_init_params = {}

        if snap is not None:
            snaps = self.compute.snapshots().list(project=project).execute()['items']
            i = list(map(lambda x: x['name']==snap, snaps)).index(True)
            url = snaps[i]['selfLink']
            # disk_init_params['sourceSnapshot'] = url
            disk_init_params = {
                'sourceSnapshot':url
            }
        else:
            disk_init_params = {
                'sourceImage':source_disk_image
            }

        # Configure the machine
        machine = "zones/{}/machineTypes/{}".format(zone,vm_type)
        if startup is not None:
            startup_script = open(
                os.path.join(os.path.dirname(__file__), startup)
            ).read()
        else:
            startup_script=None
        image_url = "http://storage.googleapis.com/gce-demo-input/photo.jpg"
        image_caption = "Ready for dessert?"
        cfg = {
            "name": name,
            "machineType": machine, #machine_type,
            # Specify the boot disk and the image to use as a source.
            "disks": [
                {
                    "boot": True,
                    "autoDelete": True,
                    "initializeParams": disk_init_params
                }
            ],
            # Specify a network interface with NAT to access the public
            # internet.
            "networkInterfaces": [
                {
                    "network": "global/networks/default",
                    "accessConfigs": [
                        {"type": "ONE_TO_ONE_NAT", "name": "External NAT"}
                    ],
                }
            ],
            # Allow the instance to access cloud storage and logging.
            "serviceAccounts": [
                {
                    "email": "default",
                    "scopes": [
                        "https://www.googleapis.com/auth/devstorage.read_write",
                        "https://www.googleapis.com/auth/logging.write",
                    ],
                }
            ],
            # Metadata is readable from the instance and allows you to
            # pass configuration from deployment scripts to instances.
            "metadata": {
                "items": [
                    {"key": "url", "value": image_url},
                    {"key": "text", "value": image_caption},
                    {"key": "bucket", "value": self.bucket},
                ]
            },
        }

        cfg['metadata']['items'].extend(
            metadata
        )

        if startup_script is not None:
            cfg['metadata']['items'].append(
                {
                    "key":"startup-script",
                    "value":startup_script
                }
            )

        return self.compute.instances().insert(
            project=project,
            zone=zone,
            body=cfg
        ).execute()

    def list_instances(
        self,
        project=None,
        zone=None
    ):
        if not project:
            project = self.project
        if not zone:
            zone = self.zone
        result = self.compute.instances().list(
            project=project,
            zone=zone
        ).execute()
        return result['items'] if 'items' in result else None

    def get_instance_ext_ip(
        self,
        name:str=None,
        project=None,
        zone=None
    ):
        if not project:
            project = self.project
        if not zone:
            zone = self.zone

        insts = self.list_instances(
            project=project,zone=zone
        )

        i = list(
            map(
                lambda x: x['name'] == name,
                insts
            )
        ).index(True)

        instance = insts[i]

        ips = []
        for interface in instance['networkInterfaces']:
            for config in interface['accessConfigs']:
                if config['type'] == 'ONE_TO_ONE_NAT':
                    ips.append(config['natIP'])

        return ips[0]
    
    def get_instance_int_ip(
        self,
        name:str=None,
        project=None,
        zone=None
    ):
        if not project:
            project = self.project
        if not zone:
            zone = self.zone
        insts = self.list_instances(
            project=project,zone=zone
        )
        i = list(
            map(
                lambda x: x['name'] == name,
                insts
            )
        ).index(True)

        instance = insts[i]
        ips = []
        for interface in instance['networkInterfaces']:
            for config in interface['accessConfigs']:
                if config['type'] == 'ONE_TO_ONE_NAT':
                    ips.append(config['natIP'])

        return ips[0]

    def delete_instance(
        self,
        name:str,
        project:str=None,
        zone:str=None
    ):
        if not project:
            project = self.project
        if not zone:
            zone = self.zone

        return (
            self.compute.instances().delete(
                project=project,
                zone=zone,
                instance=name
            ).execute()
        )

    def create_snapshot(
        self,
        instance:str,
        bod:dict=None,
        project:str=None,
        zone:str=None
    ):
        if not project:
            project = self.project
        if not zone:
            zone = self.zone

        bod_template = {
            'name':'snapshot_name',
            'description':'description_here'
        }
        if not bod:
            return bod_template

        return self.compute.disks().createSnapshot(
            project=project,
            zone=zone,
            disk=instance,
            body=bod
        ).execute()
        
    def get_snapshots(
        self,
        project:str=None
    ):
        if not project:
            project=self.project
        return self.compute.snapshots().list(
            project=project
        ).execute()

    def get_snapshot_names(
        self,
        project:str=None
    ):
        if not project:
            project=self.project

        snaps = self.get_snapshots(project)
        if not snaps.get('items',None):
            return []
        else:
            return list(
                map(
                    lambda x: x['name'],
                    snaps['items']
                )
            )

    def create_fw_rule(
        self,
        bod:dict,
        project:str=None,
        
    ):
        bod_template = {
            "name":None, #name for the rule 
            "description":None, #user defined str
            "direction":None, #"INGRESS", "EGRESS"
            "allowed":[
                {
                    'ports':[], #tcp/udp ports
                    'IPProtocol':'' #tcp or udp
                }
            ],
            'targetTags':[] #give tags for this rule
        }

        if not bod:
            return bod_template
        
        if not project:
            project = self.project
        
        self.compute.firewalls().insert(
            project=project,
            body=bod
        ).execute()
    
    def get_fw_rules(
        self,
        project:str=None,
    ):
        if not project:
            project = self.project
        return self.compute.firewalls().list(
            project=project
        ).execute()['items']
    
    def get_fw_rule_names(
        self,
        project:str=None
    ):
        return list(
            map(
                lambda x: x['name'],
                self.get_fw_rules(project)
            )
        )

    def apply_fw_tag(
        self,
        targ_instances:list,
        tags:list,
        project:str=None,
        zone:str=None
    ):
        if not project:
            project = self.project
        if not zone:
            zone = self.zone
        
        instances = self.list_instances()
        for instance in instances:
            # print(instance['name'])
            if instance['name'] in targ_instances:
                op = self.compute.instances().setTags(
                    project=project,
                    zone=zone,
                    instance=instance['name'],
                    body={
                        'fingerprint':instance['labelFingerprint'],
                        'items':tags
                    }
                ).execute()
                self.wait_for_op(op['name'])
    
    def delete_fw_rule(
        self,
        fw_rule:str,
        project:str=None
    ):
        if not project:
            project = self.project
        self.compute.firewalls().delete(
            project=project,
            firewall=fw_rule
        ).execute()


    